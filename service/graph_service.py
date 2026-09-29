import json
import os


# ============================================================
# 构建功能语义图
# ============================================================

def build_semantic_graph(
    current_functions,
    missing_functions,
    missing_relations
):
    """
    构建功能语义图。

    参数：

    current_functions：
        当前案例已有功能

    missing_functions：
        Qwen补充的功能

    missing_relations：
        最终关系集合

    返回：

    {
        "nodes": [],
        "edges": []
    }
    """

    nodes = []

    edges = []

    existing_node_ids = set()

    # ========================================================
    # 1. 添加当前已有功能
    # ========================================================

    for function in current_functions:

        if not isinstance(
            function,
            dict
        ):
            continue

        function_id = function.get(
            "id",
            ""
        )

        if not function_id:
            continue

        if function_id in existing_node_ids:
            continue

        node = dict(function)

        node["id"] = function_id

        node["nodeType"] = "existing"

        nodes.append(
            node
        )

        existing_node_ids.add(
            function_id
        )

    # ========================================================
    # 2. 添加AI补全功能
    # ========================================================

    for function in missing_functions:

        if not isinstance(
            function,
            dict
        ):
            continue

        function_id = function.get(
            "id",
            ""
        )

        if not function_id:
            continue

        if function_id in existing_node_ids:
            continue

        node = dict(function)

        node["id"] = function_id

        node["nodeType"] = "completed"

        nodes.append(
            node
        )

        existing_node_ids.add(
            function_id
        )

    # ========================================================
    # 3. 添加关系
    # ========================================================

    existing_edge_keys = set()

    for relation in missing_relations:

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

        relation_type = relation.get(
            "relation_type",
            ""
        )

        flow_object = relation.get(
            "flowObject",
            ""
        )

        if not source or not target:
            continue

        edge_key = (
            source,
            target,
            relation_type,
            flow_object
        )

        if edge_key in existing_edge_keys:
            continue

        edge = dict(
            relation
        )

        edge["source"] = source

        edge["target"] = target

        edge["relation_type"] = relation_type

        edge["flowObject"] = flow_object

        edges.append(
            edge
        )

        existing_edge_keys.add(
            edge_key
        )

    # ========================================================
    # 返回
    # ========================================================

    return {

        "nodes":
        nodes,

        "edges":
        edges

    }


# ============================================================
# 保存功能语义图
# ============================================================

def save_semantic_graph(
    graph,
    output_path
):
    """
    保存功能语义图。
    """

    directory = os.path.dirname(
        output_path
    )

    if directory:

        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            graph,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"功能语义图已保存："
        f"{output_path}"
    )