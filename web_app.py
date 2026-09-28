import time

import config

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from service.current_case_service import (
    load_current_case
)
from service.faiss_service import FAISSIndex
from service.completion_service import (
    completion,
    normalize_current_case
)
from service.graph_service import (
    build_semantic_graph
)


# ============================================================
# 创建FastAPI应用
# ============================================================

app = FastAPI(
    title="AI辅助汽车系统功能补全Demo",
    description="基于RAG+BGE+FAISS+Qwen的汽车系统功能点及关联关系补全",
    version="1.0.0"
)


# ============================================================
# 静态文件
# ============================================================

app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static"
)


# ============================================================
# 全局对象
# 程序启动时只加载一次
# ============================================================

db = None

current_case = None

normalized_case = None


# ============================================================
# 启动时加载知识库和当前案例
# ============================================================

@app.on_event("startup")
def startup_event():

    global db
    global current_case
    global normalized_case

    print()
    print("=" * 60)
    print("Web Demo启动")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. 加载FAISS知识库
    # --------------------------------------------------------

    start = time.perf_counter()

    db = FAISSIndex.load(
        config.FAISS_INDEX_PATH,
        config.FAISS_METADATA_PATH
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        f"[耗时] FAISS知识库加载："
        f"{elapsed:.3f}秒"
    )

    # --------------------------------------------------------
    # 2. 加载当前案例
    # --------------------------------------------------------

    current_case = load_current_case()

    # --------------------------------------------------------
    # 3. 标准化当前案例
    # --------------------------------------------------------

    normalized_case = normalize_current_case(
        current_case
    )

    print()

    print(
        f"当前案例："
        f"{normalized_case.get('caseId', '')}"
    )

    print(
        f"项目名称："
        f"{normalized_case.get('projectName', '')}"
    )

    print(
        f"当前功能数量："
        f"{len(normalized_case.get('functions', []))}"
    )

    print(
        f"当前关系数量："
        f"{len(normalized_case.get('relations', []))}"
    )

    print("=" * 60)


# ============================================================
# 首页
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def index():

    with open(
        "templates/index.html",
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()


# ============================================================
# 获取当前案例
# ============================================================

@app.get("/api/current-case")
def get_current_case():

    global normalized_case

    if normalized_case is None:

        return {
            "success": False,
            "message": "当前案例尚未加载",
            "case": {}
        }

    return {
        "success": True,
        "case": normalized_case
    }


# ============================================================
# 执行AI补全
# ============================================================

@app.post("/api/completion")
def run_completion():

    global db
    global current_case
    global normalized_case

    # --------------------------------------------------------
    # 检查FAISS
    # --------------------------------------------------------

    if db is None:

        return {
            "success": False,
            "message": "FAISS知识库尚未加载"
        }

    # --------------------------------------------------------
    # 检查当前案例
    # --------------------------------------------------------

    if current_case is None:

        return {
            "success": False,
            "message": "当前案例尚未加载"
        }

    print()
    print("=" * 60)
    print("收到前端AI补全请求")
    print("=" * 60)

    start = time.perf_counter()

    # ========================================================
    # 1. 调用核心补全算法
    # ========================================================

    result = completion(
        current_case,
        db,
        k=3
    )

    total_time = (
        time.perf_counter()
        - start
    )

    # ========================================================
    # 2. 获取结果
    # ========================================================

    retrieval = result.get(
        "retrieval",
        []
    )

    llm_result = result.get(
        "llm_result",
        {}
    )

    raw_llm_result = result.get(
        "raw_llm_result",
        {}
    )

    completion_result = result.get(
        "completion_result",
        {
            "functions": [],
            "relations": []
        }
    )

    # ========================================================
    # 3. 构建最终功能语义图
    #
    # 注意：
    # 语义图直接基于AI补全后的完整功能模型构建。
    #
    # 不再：
    # 当前功能 + missingFunctions
    #
    # 而是：
    # completion_result.functions
    #
    # 这样可以保证：
    #
    # 最终模型 = 语义图节点来源
    #
    # 最终关系 = 语义图边来源
    # ========================================================

    graph = build_semantic_graph(

        current_functions=
        completion_result.get(
            "functions",
            []
        ),

        # 已经把真正的补全功能合并到
        # completion_result.functions中，
        # 因此这里不再重复传missingFunctions。
        missing_functions=[],

        missing_relations=
        completion_result.get(
            "relations",
            []
        )
    )

    # ========================================================
    # 4. 获取真正的missing结果
    #
    # 注意：
    # 此时llm_result已经经过
    # filter_llm_result()过滤。
    # ========================================================

    missing_functions = llm_result.get(
        "missingFunctions",
        []
    )

    missing_relations = llm_result.get(
        "missingRelations",
        []
    )

    # ========================================================
    # 5. 获取Qwen原始结果数量
    #
    # 仅用于调试和分析。
    # 前端真正的“补全建议”使用过滤后的结果。
    # ========================================================

    raw_missing_functions = (
        raw_llm_result.get(
            "missingFunctions",
            []
        )
    )

    raw_missing_relations = (
        raw_llm_result.get(
            "missingRelations",
            []
        )
    )

    print()

    print("=" * 60)

    print("AI补全完成")

    print(
        f"总耗时："
        f"{total_time:.3f}秒"
    )

    print(
        f"当前功能："
        f"{len(normalized_case.get('functions', []))}"
    )

    print(
        f"当前关系："
        f"{len(normalized_case.get('relations', []))}"
    )

    print(
        f"Qwen原始功能候选："
        f"{len(raw_missing_functions)}"
    )

    print(
        f"Qwen原始关系候选："
        f"{len(raw_missing_relations)}"
    )

    print(
        f"过滤后真实缺失功能："
        f"{len(missing_functions)}"
    )

    print(
        f"过滤后真实缺失关系："
        f"{len(missing_relations)}"
    )

    print(
        f"最终功能数量："
        f"{len(completion_result.get('functions', []))}"
    )

    print(
        f"最终关系数量："
        f"{len(completion_result.get('relations', []))}"
    )

    print(
        f"语义图节点数量："
        f"{len(graph.get('nodes', []))}"
    )

    print(
        f"语义图边数量："
        f"{len(graph.get('edges', []))}"
    )

    print("=" * 60)

    # ========================================================
    # 6. 返回前端
    # ========================================================

    return {

        "success": True,

        "current_case":
        normalized_case,

        "retrieval":
        retrieval,

        # ----------------------------------------------------
        # 前端展示的AI补全结果
        #
        # 这里已经过滤掉：
        # 1. 当前已有功能
        # 2. 当前已有关系
        # 3. Qwen重复生成的功能/关系
        # ----------------------------------------------------

        "llm_result":
        llm_result,

        # ----------------------------------------------------
        # Qwen原始结果
        #
        # 如果前端暂时不用，也可以保留。
        # 方便后续调试模型能力。
        # ----------------------------------------------------

        "raw_llm_result":
        raw_llm_result,

        "completion_result":
        completion_result,

        "graph":
        graph,

        "statistics": {

            # 当前设计
            "currentFunctions":
            len(
                normalized_case.get(
                    "functions",
                    []
                )
            ),

            "currentRelations":
            len(
                normalized_case.get(
                    "relations",
                    []
                )
            ),

            # Qwen原始候选
            "rawMissingFunctions":
            len(
                raw_missing_functions
            ),

            "rawMissingRelations":
            len(
                raw_missing_relations
            ),

            # 过滤后的真正缺失项
            "missingFunctions":
            len(
                missing_functions
            ),

            "missingRelations":
            len(
                missing_relations
            ),

            # 最终模型
            "finalFunctions":
            len(
                completion_result.get(
                    "functions",
                    []
                )
            ),

            "finalRelations":
            len(
                completion_result.get(
                    "relations",
                    []
                )
            ),

            # 语义图
            "graphNodes":
            len(
                graph.get(
                    "nodes",
                    []
                )
            ),

            "graphEdges":
            len(
                graph.get(
                    "edges",
                    []
                )
            ),

            "totalTime":
            round(
                total_time,
                3
            )
        }
    }


# ============================================================
# 健康检查
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "ok",

        "faiss_loaded":
        db is not None,

        "current_case_loaded":
        current_case is not None,

        "normalized_case_loaded":
        normalized_case is not None

    }