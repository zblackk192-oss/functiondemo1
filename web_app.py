import time
from typing import Any, Dict

import config

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from service.current_case_service import (
    load_current_case
)

from service.faiss_service import (
    FAISSIndex
)

from service.completion_service import (
    build_confirmed_completion_result,
    completion,
    normalize_current_case
)

from service.graph_service import (
    build_semantic_graph
)

from service.result_publish_service import (
    publish_result
)

from utils.json_utils import (
    save_json
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

# 最近一次尚待人工确认的完整分析结果。
latest_analysis_result = None


# ============================================================
# 启动时加载知识库和当前案例
# ============================================================

@app.on_event("startup")
def startup_event():

    global db
    global current_case
    global normalized_case
    global latest_analysis_result

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

    latest_analysis_result = None

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
    global latest_analysis_result

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

    latest_analysis_result = result

    # ========================================================
    # 2. 保存本地result.json
    # ========================================================

    save_json(
        result,
        config.OUTPUT_PATH
    )

    print(
        f"[结果保存] 已保存到："
        f"{config.OUTPUT_PATH}"
    )

    # ========================================================
    # 3. 等待人工确认
    #
    # 此处绝不能发布。当前completion_result包含全部AI建议，
    # 用户尚未决定接受、修改或拒绝哪些候选。
    # ========================================================

    publish_status = {
        "enabled": config.RESULT_API_ENABLED,
        "success": False,
        "pending_confirmation": True,
        "message": "等待人工确认后发布"
    }

    print(
        "[结果发布] 已暂缓，等待人工确认"
    )

    total_time = (
        time.perf_counter()
        - start
    )

    # ========================================================
    # 4. 获取结果
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
    # 5. 构建最终功能语义图
    #
    # 语义图直接基于AI补全后的完整功能模型构建。
    #
    # 最终模型 = 语义图节点来源
    # 最终关系 = 语义图边来源
    # ========================================================

    graph = build_semantic_graph(

        current_functions=
        completion_result.get(
            "functions",
            []
        ),

        # 真正的补全功能已经合并到
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
    # 6. 获取真正的missing结果
    #
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
    # 7. 获取Qwen原始结果数量
    #
    # 仅用于调试和分析。
    # 前端真正的补全建议使用过滤后的结果。
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

    print(
        f"结果API推送状态："
        f"{publish_status.get('success', False)}"
    )

    print("=" * 60)

    # ========================================================
    # 8. 返回前端
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
        # 已经过滤掉：
        # 1. 当前已有功能
        # 2. 当前已有关系
        # 3. Qwen重复生成的功能/关系
        # ----------------------------------------------------

        "llm_result":
        llm_result,

        # ----------------------------------------------------
        # Qwen未经筛选的原始结果
        # ----------------------------------------------------

        "raw_llm_result":
        raw_llm_result,

        # ----------------------------------------------------
        # 合并后的最终模型
        # ----------------------------------------------------

        "completion_result":
        completion_result,

        # ----------------------------------------------------
        # 结果API推送状态
        # ----------------------------------------------------

        "publish_status":
        publish_status,

        # ----------------------------------------------------
        # 功能语义图
        # ----------------------------------------------------

        "graph":
        graph,

        # ----------------------------------------------------
        # 统计信息
        # ----------------------------------------------------

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

            # 推送状态
            "resultPublished":
            publish_status.get(
                "success",
                False
            ),

            # 完整处理耗时
            "totalTime":
            round(
                total_time,
                3
            )
        }
    }


# ============================================================
# 人工确认后发布最终模型
# ============================================================

@app.post("/api/completion/confirm")
def confirm_and_publish(
    payload: Dict[str, Any]
):

    global current_case
    global normalized_case
    global latest_analysis_result

    if latest_analysis_result is None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "当前没有等待确认的AI分析结果，"
                "请先执行AI辅助分析"
            )
        )

    if not isinstance(payload, dict):

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="确认结果必须是JSON对象"
        )

    accepted_functions = payload.get(
        "functions",
        []
    )

    accepted_relations = payload.get(
        "relations",
        []
    )

    if not isinstance(accepted_functions, list):

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="functions必须是数组"
        )

    if not isinstance(accepted_relations, list):

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="relations必须是数组"
        )

    confirmed_result = (
        build_confirmed_completion_result(
            current_case,
            accepted_functions,
            accepted_relations
        )
    )

    # result.json继续保留完整解释数据，同时把人工确认前的模型单独保留。
    confirmed_analysis_result = dict(
        latest_analysis_result
    )

    confirmed_analysis_result.setdefault(
        "proposed_completion_result",
        latest_analysis_result.get(
            "completion_result",
            {
                "functions": [],
                "relations": []
            }
        )
    )

    confirmed_analysis_result[
        "completion_result"
    ] = confirmed_result

    confirmed_analysis_result[
        "confirmation"
    ] = {
        "status": "confirmed",
        "published": False
    }

    save_json(
        confirmed_analysis_result,
        config.OUTPUT_PATH
    )

    try:

        publish_status = publish_result(
            {
                "completion_result":
                confirmed_result
            },
            normalized_case
        )

    except Exception as e:

        publish_status = {
            "enabled": config.RESULT_API_ENABLED,
            "success": False,
            "message": str(e)
        }

    published = publish_status.get(
        "success",
        False
    )

    confirmed_analysis_result[
        "confirmation"
    ] = {
        "status": "confirmed",
        "published": published,
        "publish_status": publish_status
    }

    latest_analysis_result = (
        confirmed_analysis_result
    )

    save_json(
        latest_analysis_result,
        config.OUTPUT_PATH
    )

    if not published:

        return {
            "success": False,
            "message": (
                "人工确认结果已保存，"
                "但向下游发布失败："
                f"{publish_status.get('message', '')}"
            ),
            "completion_result": confirmed_result,
            "publish_status": publish_status
        }

    print(
        "[结果发布] 人工确认完成，最终模型已推送"
    )

    return {
        "success": True,
        "message": "人工确认结果已成功发布",
        "completion_result": confirmed_result,
        "publish_status": publish_status
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
        normalized_case is not None,

        "result_api_enabled":
        config.RESULT_API_ENABLED,

        "result_api_configured":
        bool(
            config.RESULT_API_URL
            and config.RESULT_API_TOKEN
        )
    }
