import time

from service.signature_service import build_signature
from service.embedding_service import encode_text
from service.faiss_service import FAISSIndex


# ============================================================
# 工具函数
# ============================================================

def _normalize_list(value):
    """
    保证字段始终为list。
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _compact_function(function):
    """
    统一历史功能点结构。
    """

    if not isinstance(function, dict):
        return {}

    inputs = function.get(
        "inputs",
        function.get("input", [])
    )

    outputs = function.get(
        "outputs",
        function.get("output", [])
    )

    return {
        "id": function.get(
            "id",
            function.get("functionId", "")
        ),

        "name": function.get(
            "name",
            ""
        ),

        "actor": function.get("actor", ""),

        "action": function.get(
            "action",
            ""
        ),

        "object": function.get(
            "object",
            ""
        ),

        "effect": function.get(
            "effect",
            ""
        ),

        "trigger": function.get(
            "trigger",
            ""
        ),

        "condition": function.get(
            "condition",
            ""
        ),

        "preconditions": _normalize_list(
            function.get(
                "preconditions",
                []
            )
        ),

        "postconditions": _normalize_list(
            function.get(
                "postconditions",
                []
            )
        ),

        "scenario": function.get(
            "scenario",
            ""
        ),

        "constraint": function.get(
            "constraint",
            ""
        ),

        "inputs": _normalize_list(
            inputs
        ),

        "outputs": _normalize_list(
            outputs
        )
    }


def _compact_relation(relation):
    """
    统一历史关系结构。
    """

    if not isinstance(relation, dict):
        return {}

    return {
        "source": relation.get(
            "source",
            ""
        ),

        "target": relation.get(
            "target",
            ""
        ),

        "source_name": relation.get("source_name", ""),
        "target_name": relation.get("target_name", ""),

        "relation_type": relation.get(
            "relation_type",
            relation.get("type", "")
        ),

        "direction": relation.get("direction", "source_to_target"),
        "confidence": relation.get("confidence", 0.0),
        "evidence": relation.get("evidence", ""),

        "flowObject": relation.get(
            "flowObject",
            ""
        )
    }


# ============================================================
# 离线建库
# ============================================================

def build_case_vector_database(
    history_cases
):
    """
    离线构建汽车系统功能案例向量数据库。

    每一个历史功能点仍然作为一个FAISS向量。

    与旧版本相比，metadata中增加：

        caseFunctions
        caseRelations

    这样在线检索命中某个历史功能以后，
    可以恢复该功能所在案例的局部功能结构。

    metadata：

    {
        "caseId": "...",
        "projectName": "...",

        "function": {...},

        "signature": "...",

        "caseFunctions": [...],

        "caseRelations": [...]
    }
    """

    total_start_time = time.perf_counter()

    vectors = []
    metadata = []

    print("\n" + "=" * 60)
    print("开始构建向量数据库")
    print("=" * 60)

    for case in history_cases:

        case_id = case.get(
            "caseId",
            ""
        )

        project_name = case.get(
            "projectName",
            ""
        )

        case_functions = case.get(
            "functions",
            []
        )

        case_relations = case.get(
            "relations",
            []
        )

        if not isinstance(
            case_functions,
            list
        ):
            case_functions = []

        if not isinstance(
            case_relations,
            list
        ):
            case_relations = []

        for function in case_functions:

            # --------------------------------------------------
            # 1. Signature
            # --------------------------------------------------

            signature_start = (
                time.perf_counter()
            )

            signature = build_signature(
                function
            )

            signature_time = (
                time.perf_counter()
                - signature_start
            )

            print(
                f"[建库] 构造Signature："
                f"{signature_time:.3f}秒"
            )

            # --------------------------------------------------
            # 2. BGE编码
            # --------------------------------------------------

            embedding_start = (
                time.perf_counter()
            )

            vector = encode_text(
                signature
            )

            embedding_time = (
                time.perf_counter()
                - embedding_start
            )

            print(
                f"[建库] BGE编码："
                f"{embedding_time:.3f}秒"
            )

            vectors.append(
                vector
            )

            # --------------------------------------------------
            # 3. metadata
            # --------------------------------------------------

            metadata.append({
                "caseId": case_id,

                "projectName": project_name,

                "function": function,

                "signature": signature,

                # 新增
                "caseFunctions": (
                    case_functions
                ),

                # 新增
                "caseRelations": (
                    case_relations
                )
            })

    if not vectors:
        raise ValueError(
            "历史案例中没有可用于建库的功能数据"
        )

    # ------------------------------------------------------
    # 4. 创建FAISS
    # ------------------------------------------------------

    dimension = len(
        vectors[0]
    )

    db = FAISSIndex(
        dimension
    )

    db.add(
        vectors,
        metadata
    )

    total_time = (
        time.perf_counter()
        - total_start_time
    )

    print(
        f"\n[建库] 总耗时："
        f"{total_time:.3f}秒"
    )

    print(
        f"[建库] 功能向量数量："
        f"{len(vectors)}"
    )

    print("=" * 60)

    return db


# ============================================================
# 历史局部子图提取
# ============================================================

def _extract_local_subgraph(
    data
):
    """
    根据FAISS命中的历史功能，
    从该历史案例中提取：

    1. 命中功能
    2. 与命中功能直接相关的relations
    3. relation另一端的邻居功能

    即构造1-hop历史局部功能子图。
    """

    if not isinstance(
        data,
        dict
    ):
        return {
            "neighborFunctions": [],
            "relatedRelations": []
        }

    matched_function = data.get(
        "function",
        {}
    )

    if not isinstance(
        matched_function,
        dict
    ):
        matched_function = {}

    matched_id = matched_function.get(
        "id",
        matched_function.get("functionId", "")
    )

    case_functions = data.get(
        "caseFunctions",
        []
    )

    case_relations = data.get(
        "caseRelations",
        []
    )

    if not isinstance(
        case_functions,
        list
    ):
        case_functions = []

    if not isinstance(
        case_relations,
        list
    ):
        case_relations = []

    # id -> function
    function_map = {}

    for function in case_functions:

        if not isinstance(
            function,
            dict
        ):
            continue

        function_id = function.get(
            "id",
            function.get("functionId", "")
        )

        if function_id:
            function_map[
                function_id
            ] = function

    related_relations = []

    neighbor_ids = set()

    # ------------------------------------------------------
    # 找命中功能的一跳关系
    # ------------------------------------------------------

    for relation in case_relations:

        if not isinstance(
            relation,
            dict
        ):
            continue

        source = relation.get(
            "source",
            ""
        )

        target = relation.get(
            "target",
            ""
        )

        if source == matched_id:

            related_relations.append(
                _compact_relation(
                    relation
                )
            )

            if target:
                neighbor_ids.add(
                    target
                )

        elif target == matched_id:

            related_relations.append(
                _compact_relation(
                    relation
                )
            )

            if source:
                neighbor_ids.add(
                    source
                )

    # ------------------------------------------------------
    # 找邻居功能
    # ------------------------------------------------------

    neighbor_functions = []

    for neighbor_id in neighbor_ids:

        function = function_map.get(
            neighbor_id
        )

        if function:
            neighbor_functions.append(
                _compact_function(
                    function
                )
            )

    return {
        "neighborFunctions":
            neighbor_functions,

        "relatedRelations":
            related_relations
    }


# ============================================================
# 格式化检索结果
# ============================================================

def _format_retrieval_result(
    item,
    query_function=None
):
    """
    将FAISS原始结果转换为RAG结果。

    新结构：

    {
        "score": 0.81,

        "data": {

            "caseId": "CASE001",

            "function": {
                ...
            },

            "neighborFunctions": [
                ...
            ],

            "relatedRelations": [
                ...
            ]
        }
    }

    其中：

    function
        = FAISS直接命中的历史功能

    neighborFunctions
        = 与命中功能直接连接的历史功能

    relatedRelations
        = 命中功能对应的一跳历史关系
    """

    if not isinstance(
        item,
        dict
    ):
        return None

    score = item.get(
        "score",
        0
    )

    data = item.get(
        "data",
        {}
    )

    if not isinstance(
        data,
        dict
    ):
        data = {}

    original_function = data.get(
        "function",
        {}
    )

    if not isinstance(
        original_function,
        dict
    ):
        original_function = {}

    function = _compact_function(
        original_function
    )

    # signature仍然作为rawstatements
    function["rawstatements"] = (
        data.get(
            "signature",
            ""
        )
    )

    # ------------------------------------------------------
    # 提取历史局部子图
    # ------------------------------------------------------

    local_subgraph = (
        _extract_local_subgraph(
            data
        )
    )

    return {
        "score": float(
            score
        ),

        "data": {
            "caseId": data.get(
                "caseId",
                ""
            ),

            "queryFunction": (
                _compact_function(query_function)
                if isinstance(query_function, dict)
                else {}
            ),

            "function": function,

            "neighborFunctions":
                local_subgraph[
                    "neighborFunctions"
                ],

            "relatedRelations":
                local_subgraph[
                    "relatedRelations"
                ]
        }
    }


# ============================================================
# 去重
# ============================================================

def _retrieval_result_key(
    item
):
    """
    RAG结果去重键。
    """

    if not isinstance(
        item,
        dict
    ):
        return ""

    data = item.get(
        "data",
        {}
    )

    if not isinstance(
        data,
        dict
    ):
        return ""

    function = data.get(
        "function",
        {}
    )

    if not isinstance(
        function,
        dict
    ):
        function = {}

    case_id = data.get(
        "caseId",
        ""
    )

    query_function = data.get("queryFunction", {})
    if not isinstance(query_function, dict):
        query_function = {}
    query_function_id = query_function.get("id", "")

    function_id = function.get(
            "id",
            function.get("functionId", "")
        )

    return (
        f"{query_function_id}::"
        f"{case_id}::"
        f"{function_id}"
    )


def _deduplicate_results(
    results
):
    """
    多个当前功能可能检索到同一个历史功能。

    保留相似度最高的一条。
    """

    result_map = {}

    for item in results:

        key = _retrieval_result_key(
            item
        )

        if not key:
            continue

        old_item = result_map.get(
            key
        )

        if old_item is None:
            result_map[key] = item
            continue

        old_score = old_item.get(
            "score",
            0
        )

        new_score = item.get(
            "score",
            0
        )

        if new_score > old_score:
            result_map[key] = item

    deduplicated = list(
        result_map.values()
    )

    deduplicated.sort(
        key=lambda x: x.get(
            "score",
            0
        ),
        reverse=True
    )

    return deduplicated


# ============================================================
# 在线RAG检索
# ============================================================

def retrieve_top_k_cases(
    current_case,
    db,
    k=3
):
    """
    在线RAG检索。

    注意：

    k=3表示：

        每一个当前功能
        分别进行Top-3检索。

    例如当前有3个功能：

        F001 -> Top-3
        F002 -> Top-3
        F003 -> Top-3

    原始结果最多9条。

    最后对重复历史功能进行去重。

    每一个命中的历史功能都会附带：

        neighborFunctions
        relatedRelations

    从而让Qwen不仅看到历史功能，
    还能看到历史功能之间的结构关系。
    """

    total_start_time = (
        time.perf_counter()
    )

    all_results = []

    print(
        "\n" + "=" * 60
    )

    print(
        "开始在线RAG检索"
    )

    print(
        f"单功能Top-K：{k}"
    )

    print(
        "=" * 60
    )

    current_functions = (
        current_case.get(
            "functions",
            []
        )
    )

    if not isinstance(
        current_functions,
        list
    ):
        current_functions = []

    for function in current_functions:

        if not isinstance(
            function,
            dict
        ):
            continue

        function_id = function.get(
            "id",
            function.get("functionId", "")
        )

        function_name = function.get(
            "name",
            ""
        )

        print(
            f"\n检索功能："
            f"{function_id} "
            f"{function_name}"
        )

        # --------------------------------------------------
        # 1. Signature
        # --------------------------------------------------

        signature_start = (
            time.perf_counter()
        )

        signature = build_signature(
            function
        )

        signature_time = (
            time.perf_counter()
            - signature_start
        )

        print(
            f"[耗时] Signature构造："
            f"{signature_time:.3f}秒"
        )

        # --------------------------------------------------
        # 2. BGE
        # --------------------------------------------------

        embedding_start = (
            time.perf_counter()
        )

        vector = encode_text(
            signature
        )

        embedding_time = (
            time.perf_counter()
            - embedding_start
        )

        print(
            f"[耗时] BGE编码："
            f"{embedding_time:.3f}秒"
        )

        # --------------------------------------------------
        # 3. FAISS Top-K
        # --------------------------------------------------

        search_start = (
            time.perf_counter()
        )

        results = db.search(
            vector,
            k
        )

        search_time = (
            time.perf_counter()
            - search_start
        )

        print(
            f"[耗时] FAISS Top-{k}检索："
            f"{search_time:.3f}秒"
        )

        # --------------------------------------------------
        # 4. 格式化
        # --------------------------------------------------

        for item in results:

            formatted_item = (
                _format_retrieval_result(
                    item,
                    query_function=function
                )
            )

            if formatted_item is None:
                continue

            all_results.append(
                formatted_item
            )

    # ------------------------------------------------------
    # 5. 去重
    # ------------------------------------------------------

    before_count = len(
        all_results
    )

    all_results = (
        _deduplicate_results(
            all_results
        )
    )

    after_count = len(
        all_results
    )

    print(
        f"\n[RAG] 去重前："
        f"{before_count}"
    )

    print(
        f"[RAG] 去重后："
        f"{after_count}"
    )

    # ------------------------------------------------------
    # 6. 打印历史结构信息
    # ------------------------------------------------------

    for index, item in enumerate(
        all_results,
        start=1
    ):

        data = item.get(
            "data",
            {}
        )

        function = data.get(
            "function",
            {}
        )

        neighbors = data.get(
            "neighborFunctions",
            []
        )

        relations = data.get(
            "relatedRelations",
            []
        )

        print(
            f"[RAG-{index}] "
            f"{data.get('caseId', '')} | "
            f"{function.get('id', '')} "
            f"{function.get('name', '')} | "
            f"score={item.get('score', 0):.4f} | "
            f"邻居={len(neighbors)} | "
            f"关系={len(relations)}"
        )

    total_time = (
        time.perf_counter()
        - total_start_time
    )

    print(
        f"\n[RAG] 在线检索总耗时："
        f"{total_time:.3f}秒"
    )

    print(
        "=" * 60
    )

    return all_results