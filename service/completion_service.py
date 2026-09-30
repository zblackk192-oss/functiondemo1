import time

import config

from service.retrieval_service import retrieve_top_k_cases
from service.prompt_service import build_completion_prompt
from service.llm_service import call_qwen
from service.json_parser_service import parse_llm_json


# ============================================================
# 通用工具
# ============================================================

def normalize_list(value):
    """
    保证字段始终为list。
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def normalize_text(value):
    """
    用于功能点、关系去重比较。
    """

    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


# ============================================================
# 功能点标准化
# ============================================================

def normalize_function(
    function,
    index=None
):
    """
    将功能点标准化为统一结构。

    注意：
    不删除Qwen生成的扩展证据字段：

        requirementEvidence
        historyEvidence
        evidenceType
        reason
        confidence
    """

    if not isinstance(
        function,
        dict
    ):
        return None

    # 保留原始字段
    result = dict(
        function
    )

    # 兼容旧文件，但标准化结果中不保留旧名称。
    legacy_id = result.pop("functionId", "")

    # --------------------------------------------------------
    # id
    # --------------------------------------------------------

    if not result.get("id"):
        if legacy_id:
            result["id"] = legacy_id
        elif index is not None:
            result["id"] = (
                f"F{index:03d}"
            )

    # --------------------------------------------------------
    # name
    # --------------------------------------------------------

    if not result.get("name"):
        result["name"] = result.get(
            "functionName",
            ""
        )

    # --------------------------------------------------------
    # input / output兼容
    # --------------------------------------------------------

    if "inputs" not in result:
        result["inputs"] = result.get(
            "input",
            []
        )

    if "outputs" not in result:
        result["outputs"] = result.get(
            "output",
            []
        )

    result["inputs"] = normalize_list(
        result.get(
            "inputs",
            []
        )
    )

    result["outputs"] = normalize_list(
        result.get(
            "outputs",
            []
        )
    )

    # --------------------------------------------------------
    # 基础字符串字段
    # --------------------------------------------------------

    for field in [
        "name",
        "actor",
        "action",
        "object",
        "effect",
        "trigger",
        "condition",
        "scenario",
        "constraint"
    ]:
        value = result.get(
            field,
            ""
        )

        if value is None:
            value = ""

        result[field] = str(
            value
        )

    # --------------------------------------------------------
    # 数组字段
    # --------------------------------------------------------

    for field in [
        "preconditions",
        "postconditions"
    ]:
        result[field] = normalize_list(
            result.get(
                field,
                []
            )
        )

    # --------------------------------------------------------
    # RAG证据字段
    # --------------------------------------------------------

    result.setdefault(
        "requirementEvidence",
        ""
    )

    result["historyEvidence"] = (
        normalize_list(
            result.get(
                "historyEvidence",
                []
            )
        )
    )

    result.setdefault(
        "evidenceType",
        ""
    )

    result.setdefault(
        "reason",
        ""
    )

    # confidence允许为空
    confidence = result.get(
        "confidence",
        0.0
    )

    try:
        confidence = float(
            confidence
        )
    except (
        TypeError,
        ValueError
    ):
        confidence = 0.0

    # 限制0~1
    confidence = max(
        0.0,
        min(
            1.0,
            confidence
        )
    )

    result["confidence"] = (
        confidence
    )

    return result


# ============================================================
# 关系标准化
# ============================================================

def normalize_relation(
    relation
):
    """
    统一关系结构。

    与旧版本不同：
    保留Qwen输出的历史证据字段。
    """

    if not isinstance(
        relation,
        dict
    ):
        return None

    source = relation.get(
        "source",
        relation.get(
            "from",
            ""
        )
    )

    target = relation.get(
        "target",
        relation.get(
            "to",
            ""
        )
    )

    source = normalize_text(
        source
    )

    target = normalize_text(
        target
    )

    if not source or not target:
        return None

    # 先复制，避免丢失证据字段
    result = dict(
        relation
    )

    # 兼容旧数据，但标准化结果中不保留旧名称。
    legacy_relation_type = result.pop("type", "")

    result["source"] = source
    result["target"] = target

    result["relation_type"] = normalize_text(
        relation.get(
            "relation_type",
            legacy_relation_type or "dependency"
        )
    )

    if not result["relation_type"]:
        result["relation_type"] = (
            "dependency"
        )

    result["flowObject"] = (
        relation.get(
            "flowObject",
            relation.get(
                "object",
                ""
            )
        )
        or ""
    )

    # --------------------------------------------------------
    result.setdefault("source_name", "")
    result.setdefault("target_name", "")
    result.setdefault("direction", "source_to_target")
    result.setdefault("evidence", "")

    # RAG证据字段
    # --------------------------------------------------------

    result["historyEvidence"] = (
        normalize_list(
            result.get(
                "historyEvidence",
                []
            )
        )
    )

    result.setdefault(
        "evidenceType",
        ""
    )

    result.setdefault(
        "reason",
        ""
    )

    confidence = result.get(
        "confidence",
        0.0
    )

    try:
        confidence = float(
            confidence
        )
    except (
        TypeError,
        ValueError
    ):
        confidence = 0.0

    result["confidence"] = max(
        0.0,
        min(
            1.0,
            confidence
        )
    )

    return result


# ============================================================
# 当前案例标准化
# ============================================================

def normalize_current_case(
    current_case
):
    """
    当前案例标准化。

    当前需求语义：
        raw_text
        function_points
        events

    当前设计基线：
        functions
        relations
    """

    if not isinstance(
        current_case,
        dict
    ):
        return {
            "caseId": "CURRENT001",
            "projectName": "",
            "raw_text": "",
            "function_points": [],
            "events": [],
            "functions": [],
            "relations": []
        }

    normalized_case = dict(
        current_case
    )

    # --------------------------------------------------------
    # functions
    # --------------------------------------------------------

    raw_functions = current_case.get(
        "functions",
        []
    )

    if not isinstance(
        raw_functions,
        list
    ):
        raw_functions = []

    functions = []

    for index, function in enumerate(
        raw_functions,
        start=1
    ):
        normalized = (
            normalize_function(
                function,
                index
            )
        )

        if normalized:
            functions.append(
                normalized
            )

    normalized_case[
        "functions"
    ] = functions

    # --------------------------------------------------------
    # relations
    # --------------------------------------------------------

    raw_relations = current_case.get(
        "relations",
        []
    )

    if not isinstance(
        raw_relations,
        list
    ):
        raw_relations = []

    relations = []

    for relation in raw_relations:
        normalized = (
            normalize_relation(
                relation
            )
        )

        if normalized:
            relations.append(
                normalized
            )

    normalized_case[
        "relations"
    ] = relations

    # --------------------------------------------------------
    # raw_text
    # --------------------------------------------------------

    raw_text = normalized_case.get(
        "raw_text",
        ""
    )

    if raw_text is None:
        raw_text = ""

    normalized_case[
        "raw_text"
    ] = str(
        raw_text
    )

    # --------------------------------------------------------
    # function_points
    # --------------------------------------------------------

    normalized_case[
        "function_points"
    ] = normalize_list(
        normalized_case.get(
            "function_points",
            []
        )
    )

    # --------------------------------------------------------
    # events
    # --------------------------------------------------------

    normalized_case[
        "events"
    ] = normalize_list(
        normalized_case.get(
            "events",
            []
        )
    )

    return normalized_case


# ============================================================
# 功能语义签名
# ============================================================

def function_signature(
    function
):
    """
    用于判断两个功能是否已经存在。

    action + object + effect
    """

    if not isinstance(
        function,
        dict
    ):
        return (
            "",
            "",
            ""
        )

    return (
        normalize_text(
            function.get(
                "action",
                ""
            )
        ),

        normalize_text(
            function.get(
                "object",
                ""
            )
        ),

        normalize_text(
            function.get(
                "effect",
                ""
            )
        )
    )


# ============================================================
# 关系唯一Key
# ============================================================

def relation_key(
    relation
):
    """
    source + target + type

    flowObject不参与核心重复判断。
    """

    if not isinstance(
        relation,
        dict
    ):
        return (
            "",
            "",
            ""
        )

    return (
        normalize_text(
            relation.get(
                "source",
                ""
            )
        ),

        normalize_text(
            relation.get(
                "target",
                ""
            )
        ),

        normalize_text(
            relation.get(
                "relation_type",
                ""
            )
        )
    )


# ============================================================
# 判断功能是否已经存在
# ============================================================

def function_already_exists(
    candidate,
    current_functions
):
    """
    判断规则：

    1. id相同
    2. action + object + effect完全相同
    """

    if not isinstance(
        candidate,
        dict
    ):
        return False

    candidate_id = normalize_text(
        candidate.get(
            "id",
            ""
        )
    )

    candidate_signature = (
        function_signature(
            candidate
        )
    )

    for current in current_functions:

        if not isinstance(
            current,
            dict
        ):
            continue

        current_id = normalize_text(
            current.get(
                "id",
                ""
            )
        )

        # ----------------------------------------------------
        # ID相同
        # ----------------------------------------------------

        if (
            candidate_id
            and current_id
            and candidate_id
            == current_id
        ):
            return True

        # ----------------------------------------------------
        # 语义签名相同
        # ----------------------------------------------------

        current_signature = (
            function_signature(
                current
            )
        )

        if (
            candidate_signature
            == current_signature
            and all(
                candidate_signature
            )
        ):
            return True

    return False


# ============================================================
# 为Qwen缺失功能分配合法ID
# ============================================================

def assign_missing_function_ids(
    current_functions,
    missing_functions
):
    """
    确保Qwen生成的新功能拥有合法且不冲突的id。

    非常重要：

    missingRelations可能引用这些新功能。

    因此必须在关系过滤之前完成ID处理。
    """

    existing_ids = {
        normalize_text(
            function.get(
                "id",
                ""
            )
        )
        for function
        in current_functions
        if isinstance(
            function,
            dict
        )
        and function.get(
            "id"
        )
    }

    assigned_functions = []

    next_number = 1

    for function in missing_functions:

        normalized = (
            normalize_function(
                function
            )
        )

        if not normalized:
            continue

        function_id = normalize_text(
            normalized.get(
                "id",
                ""
            )
        )

        # ----------------------------------------------------
        # ID为空或与当前设计冲突
        # ----------------------------------------------------

        if (
            not function_id
            or function_id
            in existing_ids
        ):

            while (
                f"F{next_number:03d}"
                in existing_ids
            ):
                next_number += 1

            function_id = (
                f"F{next_number:03d}"
            )

            next_number += 1

            normalized[
                "id"
            ] = function_id

        existing_ids.add(
            function_id
        )

        assigned_functions.append(
            normalized
        )

    return assigned_functions


# ============================================================
# Qwen候选过滤
# ============================================================

UPDATABLE_FUNCTION_FIELDS = {
    "name", "actor", "action", "object", "effect", "trigger",
    "condition", "inputs", "outputs", "preconditions",
    "postconditions", "scenario", "constraint"
}

LIST_FUNCTION_FIELDS = {
    "inputs", "outputs", "preconditions", "postconditions"
}

MISSING_TEXT_VALUES = {"", "未显式说明"}
GENERIC_ACTOR_VALUES = {"系统", "模块", "控制器"}


def is_missing_field_value(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in MISSING_TEXT_VALUES
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def normalize_function_update(update, current_function_map):
    """只允许补已有功能的空字段，不覆盖已有内容。"""

    if not isinstance(update, dict):
        return None

    function_id = normalize_text(update.get("id", ""))
    current_function = current_function_map.get(function_id)

    if not function_id or not current_function:
        return None

    raw_fields = update.get("fields", {})
    if not isinstance(raw_fields, dict):
        raw_fields = {}

    completed_fields = {}

    for field in UPDATABLE_FUNCTION_FIELDS:
        if field not in raw_fields:
            continue
        if not is_missing_field_value(current_function.get(field)):
            continue

        value = raw_fields.get(field)
        if is_missing_field_value(value):
            continue

        if field in LIST_FUNCTION_FIELDS:
            value = normalize_list(value)
        else:
            value = str(value).strip()

        if field == "actor" and value in GENERIC_ACTOR_VALUES:
            continue

        completed_fields[field] = value

    if not completed_fields:
        return None

    confidence = update.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    if confidence < 0.55:
        return None

    return {
        "id": function_id,
        "fields": completed_fields,
        "requirementEvidence": update.get("requirementEvidence", ""),
        "historyEvidence": normalize_list(
            update.get("historyEvidence", [])
        ),
        "evidenceType": update.get(
            "evidenceType",
            "requirement_only"
        ),
        "reason": update.get("reason", ""),
        "confidence": confidence
    }


def filter_function_updates(current_functions, raw_updates):
    if not isinstance(raw_updates, list):
        raw_updates = []

    current_function_map = {
        normalize_text(function.get("id", "")): function
        for function in current_functions
        if isinstance(function, dict) and function.get("id")
    }

    update_map = {}

    for update in raw_updates:
        normalized = normalize_function_update(
            update,
            current_function_map
        )
        if not normalized:
            continue

        function_id = normalized["id"]
        if function_id not in update_map:
            update_map[function_id] = normalized
            continue

        old_update = update_map[function_id]
        combined_fields = dict(old_update["fields"])
        combined_fields.update(normalized["fields"])

        if normalized["confidence"] > old_update["confidence"]:
            normalized["fields"] = combined_fields
            update_map[function_id] = normalized
        else:
            old_update["fields"] = combined_fields

    return list(update_map.values())


def apply_function_updates(functions, function_updates):
    """将已通过校验的字段更新应用到已有功能。"""

    update_map = {
        update.get("id"): update
        for update in function_updates
        if isinstance(update, dict) and update.get("id")
    }

    updated_functions = []

    for function in functions:
        updated = dict(function)
        update = update_map.get(updated.get("id"))

        if update:
            fields = update.get("fields", {})
            if isinstance(fields, dict):
                for field, value in fields.items():
                    if field not in UPDATABLE_FUNCTION_FIELDS:
                        continue
                    if not is_missing_field_value(updated.get(field)):
                        continue
                    updated[field] = value

            updated.setdefault("fieldCompletionEvidence", [])
            updated["fieldCompletionEvidence"].append({
                "fields": list(fields.keys()),
                "requirementEvidence": update.get(
                    "requirementEvidence", ""
                ),
                "historyEvidence": update.get("historyEvidence", []),
                "evidenceType": update.get("evidenceType", ""),
                "reason": update.get("reason", ""),
                "confidence": update.get("confidence", 0.0)
            })

        updated_functions.append(updated)

    return updated_functions

def filter_llm_result(
    current_case,
    llm_result
):
    """
    对Qwen候选补全进行一致性校验。

    关键规则：

    1. 已有功能不重复补。
    2. 已有关系不重复补。
    3. 新补功能可以作为新关系端点。
    4. 保留RAG证据字段。
    """

    if not isinstance(
        llm_result,
        dict
    ):
        llm_result = {}

    current_functions = (
        current_case.get(
            "functions",
            []
        )
    )

    current_relations = (
        current_case.get(
            "relations",
            []
        )
    )

    if not isinstance(
        current_functions,
        list
    ):
        current_functions = []

    if not isinstance(
        current_relations,
        list
    ):
        current_relations = []

    # ========================================================
    # 1. 当前功能标准化
    # ========================================================

    normalized_current_functions = []

    for index, function in enumerate(
        current_functions,
        start=1
    ):
        normalized = (
            normalize_function(
                function,
                index
            )
        )

        if normalized:
            normalized_current_functions.append(
                normalized
            )

    # ========================================================
    # ========================================================
    # 已有功能缺失字段候选
    # ========================================================

    raw_function_updates = llm_result.get("functionUpdates", [])
    filtered_function_updates = filter_function_updates(
        normalized_current_functions,
        raw_function_updates
    )
    # 2. 当前关系Key
    # ========================================================

    existing_relation_keys = set()

    for relation in current_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if normalized:
            existing_relation_keys.add(
                relation_key(
                    normalized
                )
            )

    # ========================================================
    # 3. Qwen候选功能
    # ========================================================

    raw_missing_functions = (
        llm_result.get(
            "missingFunctions",
            []
        )
    )

    if not isinstance(
        raw_missing_functions,
        list
    ):
        raw_missing_functions = []

    filtered_functions = []

    for function in raw_missing_functions:

        normalized = (
            normalize_function(
                function
            )
        )

        if not normalized:
            continue

        # ----------------------------------------------------
        # 已存在于当前设计
        # ----------------------------------------------------

        if function_already_exists(
            normalized,
            normalized_current_functions
        ):
            print(
                "[过滤] Qwen功能点已经存在："
                f"{normalized.get('id', '')} "
                f"{normalized.get('name', '')}"
            )

            continue

        # ----------------------------------------------------
        # Qwen自己重复
        # ----------------------------------------------------

        if function_already_exists(
            normalized,
            filtered_functions
        ):
            print(
                "[过滤] Qwen重复功能点："
                f"{normalized.get('name', '')}"
            )

            continue

        filtered_functions.append(
            normalized
        )

    # ========================================================
    # 4. 为缺失功能处理ID
    # ========================================================

    filtered_functions = (
        assign_missing_function_ids(
            normalized_current_functions,
            filtered_functions
        )
    )

    # ========================================================
    # 5. 构造合法关系端点集合
    # ========================================================

    current_function_ids = {
        normalize_text(
            function.get(
                "id",
                ""
            )
        )
        for function
        in normalized_current_functions
        if function.get(
            "id"
        )
    }

    missing_function_ids = {
        normalize_text(
            function.get(
                "id",
                ""
            )
        )
        for function
        in filtered_functions
        if function.get(
            "id"
        )
    }

    # --------------------------------------------------------
    # 关键：
    #
    # 当前已有功能
    # +
    # 本轮新增功能
    #
    # 都可以成为relation端点
    # --------------------------------------------------------

    valid_function_ids = (
        current_function_ids
        |
        missing_function_ids
    )

    print(
        "[过滤] 当前功能ID："
        f"{sorted(current_function_ids)}"
    )

    print(
        "[过滤] 新增功能ID："
        f"{sorted(missing_function_ids)}"
    )

    # ========================================================
    # 6. Qwen候选关系
    # ========================================================

    raw_missing_relations = (
        llm_result.get(
            "missingRelations",
            []
        )
    )

    if not isinstance(
        raw_missing_relations,
        list
    ):
        raw_missing_relations = []

    filtered_relations = []

    for relation in raw_missing_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if not normalized:
            continue

        source = normalize_text(
            normalized.get(
                "source",
                ""
            )
        )

        target = normalize_text(
            normalized.get(
                "target",
                ""
            )
        )

        # ----------------------------------------------------
        # 禁止自环
        # ----------------------------------------------------

        if source == target:

            print(
                "[过滤] 忽略自环关系："
                f"{source} -> {target}"
            )

            continue

        # ----------------------------------------------------
        # 端点检查
        # ----------------------------------------------------

        if (
            source not in valid_function_ids
            or target
            not in valid_function_ids
        ):
            print(
                "[过滤] 关系端点不存在："
                f"{source} -> {target}"
            )

            continue

        key = relation_key(
            normalized
        )

        # ----------------------------------------------------
        # 当前已经存在
        # ----------------------------------------------------

        if key in existing_relation_keys:

            print(
                "[过滤] Qwen关系已经存在："
                f"{source} -> {target} "
                f"({normalized.get('relation_type', '')})"
            )

            continue

        # ----------------------------------------------------
        # Qwen自己重复
        # ----------------------------------------------------

        if any(
            relation_key(
                item
            ) == key
            for item
            in filtered_relations
        ):
            print(
                "[过滤] Qwen重复关系："
                f"{source} -> {target}"
            )

            continue

        filtered_relations.append(
            normalized
        )

    # ========================================================
    # 7. 最终过滤结果
    # ========================================================

    filtered_result = dict(
        llm_result
    )

    filtered_result["functionUpdates"] = (
        filtered_function_updates
    )

    filtered_result[
        "missingFunctions"
    ] = filtered_functions

    filtered_result[
        "missingRelations"
    ] = filtered_relations

    return filtered_result


# ============================================================
# 构建AI初步补全模型
# ============================================================

def build_completion_result(
    current_case,
    llm_result
):
    """
    当前设计
        +
    AI真正缺失功能
        +
    AI真正缺失关系
    """

    current_functions = (
        current_case.get(
            "functions",
            []
        )
    )

    current_relations = (
        current_case.get(
            "relations",
            []
        )
    )

    function_updates = llm_result.get("functionUpdates", [])
    if not isinstance(function_updates, list):
        function_updates = []
    missing_functions = (
        llm_result.get(
            "missingFunctions",
            []
        )
    )

    missing_relations = (
        llm_result.get(
            "missingRelations",
            []
        )
    )

    # ========================================================
    # 功能
    # ========================================================

    functions = []

    for index, function in enumerate(
        current_functions,
        start=1
    ):
        normalized = (
            normalize_function(
                function,
                index
            )
        )

        if normalized:
            functions.append(
                normalized
            )

    functions = apply_function_updates(
        functions,
        function_updates
    )
    existing_ids = {
        function.get(
            "id"
        )
        for function
        in functions
        if function.get(
            "id"
        )
    }

    for function in missing_functions:

        normalized = (
            normalize_function(
                function
            )
        )

        if not normalized:
            continue

        function_id = (
            normalized.get(
                "id"
            )
        )

        if (
            not function_id
            or function_id
            in existing_ids
        ):
            number = 1

            while (
                f"F{number:03d}"
                in existing_ids
            ):
                number += 1

            function_id = (
                f"F{number:03d}"
            )

            normalized[
                "id"
            ] = function_id

        functions.append(
            normalized
        )

        existing_ids.add(
            function_id
        )

    # ========================================================
    # 关系
    # ========================================================

    relations = []

    for relation in current_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if normalized:
            relations.append(
                normalized
            )

    existing_relation_keys = {
        relation_key(
            relation
        )
        for relation
        in relations
    }

    final_function_ids = {
        function.get(
            "id"
        )
        for function
        in functions
        if function.get(
            "id"
        )
    }

    for relation in missing_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if not normalized:
            continue

        source = normalized[
            "source"
        ]

        target = normalized[
            "target"
        ]

        if (
            source
            not in final_function_ids
        ):
            continue

        if (
            target
            not in final_function_ids
        ):
            continue

        key = relation_key(
            normalized
        )

        if key in existing_relation_keys:
            continue

        relations.append(
            normalized
        )

        existing_relation_keys.add(
            key
        )

    return {
        "functions": functions,
        "relations": relations
    }


# ============================================================
# 人工确认后的最终结果
# ============================================================

def build_confirmed_completion_result(
    current_case,
    accepted_functions,
    accepted_relations
):
    """
    根据人工确认结果生成最终模型。

    当前原始设计始终保留。
    """

    normalized_case = (
        normalize_current_case(
            current_case
        )
    )

    current_functions = (
        normalized_case.get(
            "functions",
            []
        )
    )

    current_relations = (
        normalized_case.get(
            "relations",
            []
        )
    )

    if not isinstance(
        accepted_functions,
        list
    ):
        accepted_functions = []

    if not isinstance(
        accepted_relations,
        list
    ):
        accepted_relations = []

    # ========================================================
    # 功能
    # ========================================================

    functions = []

    for index, function in enumerate(
        current_functions,
        start=1
    ):
        normalized = (
            normalize_function(
                function,
                index
            )
        )

        if normalized:
            functions.append(
                normalized
            )

    function_map = {
        function.get(
            "id"
        ): function
        for function
        in functions
        if function.get(
            "id"
        )
    }

    for function in accepted_functions:

        normalized = (
            normalize_function(
                function
            )
        )

        if not normalized:
            continue

        function_id = (
            normalized.get(
                "id"
            )
        )

        if not function_id:

            number = 1

            while (
                f"F{number:03d}"
                in function_map
            ):
                number += 1

            function_id = (
                f"F{number:03d}"
            )

            normalized[
                "id"
            ] = function_id

        function_map[
            function_id
        ] = normalized

    functions = list(
        function_map.values()
    )

    final_function_ids = {
        function.get(
            "id"
        )
        for function
        in functions
        if function.get(
            "id"
        )
    }

    # ========================================================
    # 关系
    # ========================================================

    relations = []

    for relation in current_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if normalized:
            relations.append(
                normalized
            )

    relation_keys = {
        relation_key(
            relation
        )
        for relation
        in relations
    }

    for relation in accepted_relations:

        normalized = (
            normalize_relation(
                relation
            )
        )

        if not normalized:
            continue

        source = normalized[
            "source"
        ]

        target = normalized[
            "target"
        ]

        if (
            source
            not in final_function_ids
        ):
            continue

        if (
            target
            not in final_function_ids
        ):
            continue

        key = relation_key(
            normalized
        )

        if key in relation_keys:
            continue

        relations.append(
            normalized
        )

        relation_keys.add(
            key
        )

    return {
        "functions": functions,
        "relations": relations
    }


# ============================================================
# 知识库检索统计
# ============================================================

def print_rag_structure_statistics(
    retrieved
):
    """
    打印知识库API返回的架构子图摘要。
    """

    for index, item in enumerate(
        retrieved,
        start=1
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        print(
            f"[知识库结构-{index}] "
            f"{item.get('subgraph_id', '')} | "
            f"{item.get('architecture_id', '')} | "
            f"{item.get('title', '')} | "
            f"view={item.get('view_type', '')} | "
            f"rank={item.get('rank', 0.0)}"
        )

    print(
        "[知识库结构统计] "
        f"架构子图命中：{len(retrieved)}"
    )


# ============================================================
# 主补全流程
# ============================================================

def completion(
    current_case,
    db=None,
    k=None
):
    """
    知识库API + Qwen功能点及关联关系补全。

    新流程：

        当前需求
            +
        当前设计
            ↓
        知识库POST /api/query + FTS5
            ↓
        架构子图matches
            ↓
        证据化Prompt
            ↓
        Qwen候选
            ↓
        一致性过滤
            ↓
        AI补全结果
    """

    total_start_time = (
        time.perf_counter()
    )

    # ========================================================
    # 1. 当前案例标准化
    # ========================================================

    start = time.perf_counter()

    normalized_case = (
        normalize_current_case(
            current_case
        )
    )

    print(
        f"[耗时] 当前设计输入标准化："
        f"{time.perf_counter() - start:.3f}秒"
    )

    print(
        f"[当前设计] "
        f"{normalized_case.get('caseId', '')}"
    )

    print(
        f"[当前设计] 功能点数量："
        f"{len(normalized_case.get('functions', []))}"
    )

    print(
        f"[当前设计] 关系数量："
        f"{len(normalized_case.get('relations', []))}"
    )

    print(
        f"[当前需求] raw_text长度："
        f"{len(normalized_case.get('raw_text', ''))}"
    )

    for function in normalized_case.get(
        "functions",
        []
    ):
        print(
            f"  - "
            f"{function.get('id', '')} "
            f"{function.get('name', '')}"
        )

    # ========================================================
    # 2. 知识库API检索
    # ========================================================

    start = time.perf_counter()

    retrieved = retrieve_top_k_cases(
        normalized_case,
        db,
        k=(
            config.KNOWLEDGE_API_TOP_K
            if k is None
            else k
        )
    )

    print(
        f"[耗时] 知识库API检索阶段："
        f"{time.perf_counter() - start:.3f}秒"
    )

    print(
        f"[知识库API] 检索结果数量："
        f"{len(retrieved)}"
    )

    # --------------------------------------------------------
    # 非常重要：
    # 检查架构子图是否真的进入retrieval
    # --------------------------------------------------------

    print_rag_structure_statistics(
        retrieved
    )

    # ========================================================
    # 3. 构建Prompt
    # ========================================================

    start = time.perf_counter()

    # --------------------------------------------------------
    # 关键修改：
    #
    # 直接把知识库API标准化后的matches交给prompt_service。
    # --------------------------------------------------------

    prompt = build_completion_prompt(
        raw_text=normalized_case.get(
            "raw_text",
            ""
        ),

        current_functions=normalized_case.get(
            "functions",
            []
        ),

        current_relations=normalized_case.get(
            "relations",
            []
        ),

        history_functions=retrieved,

        function_points=normalized_case.get(
            "function_points",
            []
        ),

        events=normalized_case.get(
            "events",
            []
        )
    )

    print(
        f"[耗时] Prompt阶段："
        f"{time.perf_counter() - start:.3f}秒"
    )

    print(
        f"[知识库API] Prompt架构子图数量："
        f"{len(retrieved)}"
    )

    # ========================================================
    # 4. Qwen
    # ========================================================

    start = time.perf_counter()

    try:

        llm_response = call_qwen(
            prompt
        )

        raw_llm_result = (
            parse_llm_json(
                llm_response
            )
        )

        if not isinstance(
            raw_llm_result,
            dict
        ):
            raw_llm_result = {}

        raw_llm_result.setdefault(
            "functionUpdates",
            []
        )
        raw_llm_result.setdefault(
            "missingFunctions",
            []
        )

        raw_llm_result.setdefault(
            "missingRelations",
            []
        )

        # 知识库已经命中架构子图、但模型首轮三个数组全空时，
        # 不能直接把“空”当作最终结论。用排序靠前的子图再复核一次，
        # 解决知识文本稀释注意力以及模型过度保守的问题。
        first_pass_is_empty = not any(
            isinstance(
                raw_llm_result.get(key),
                list
            )
            and raw_llm_result.get(key)
            for key in (
                "functionUpdates",
                "missingFunctions",
                "missingRelations"
            )
        )

        if (
            config.QWEN_EMPTY_RESULT_RECHECK_ENABLED
            and first_pass_is_empty
            and retrieved
        ):
            print(
                "[Qwen复核] 知识库命中非空但首轮补全为空，"
                "启动一次架构子图复核"
            )

            recovery_prompt = build_completion_prompt(
                raw_text=normalized_case.get(
                    "raw_text",
                    ""
                ),
                current_functions=normalized_case.get(
                    "functions",
                    []
                ),
                current_relations=normalized_case.get(
                    "relations",
                    []
                ),
                history_functions=retrieved,
                function_points=normalized_case.get(
                    "function_points",
                    []
                ),
                events=normalized_case.get(
                    "events",
                    []
                ),
                recovery_mode=True
            )

            recovery_response = call_qwen(
                recovery_prompt
            )

            recovery_result = parse_llm_json(
                recovery_response
            )

            if isinstance(
                    recovery_result,
                    dict
            ):
                recovery_result.setdefault(
                    "functionUpdates",
                    []
                )
                recovery_result.setdefault(
                    "missingFunctions",
                    []
                )
                recovery_result.setdefault(
                    "missingRelations",
                    []
                )

                recovery_has_candidates = any(
                    isinstance(
                        recovery_result.get(key),
                        list
                    )
                    and recovery_result.get(key)
                    for key in (
                        "functionUpdates",
                        "missingFunctions",
                        "missingRelations"
                    )
                )

                if recovery_has_candidates:
                    raw_llm_result = recovery_result

                    print(
                        "[Qwen复核] 已获得可审查补全候选"
                    )
                else:
                    print(
                        "[Qwen复核] 复核后仍无有证据候选"
                    )

        # 大模型即使偶尔返回旧字段名，也在进入结果前统一为最终标准。
        raw_functions = raw_llm_result.get("missingFunctions", [])
        raw_relations = raw_llm_result.get("missingRelations", [])

        if not isinstance(raw_functions, list):
            raw_functions = []

        if not isinstance(raw_relations, list):
            raw_relations = []

        raw_llm_result["missingFunctions"] = [
            normalized
            for index, function in enumerate(raw_functions, start=1)
            for normalized in [normalize_function(function, index)]
            if normalized
        ]

        raw_llm_result["missingRelations"] = [
            normalized
            for relation in raw_relations
            for normalized in [normalize_relation(relation)]
            if normalized
        ]

    except Exception as e:

        print(
            "[错误] Qwen调用失败"
        )

        print(
            f"[错误信息] {e}"
        )

        raw_llm_result = {
            "functionUpdates": [],
            "missingFunctions": [],
            "missingRelations": []
        }

    print(
        f"[耗时] Qwen阶段："
        f"{time.perf_counter() - start:.3f}秒"
    )

    print(
        "[Qwen原始结果] "
        f"字段更新："
        f"{len(raw_llm_result.get('functionUpdates', []))}"
        f"，"
        f"功能："
        f"{len(raw_llm_result.get('missingFunctions', []))}"
        f"，关系："
        f"{len(raw_llm_result.get('missingRelations', []))}"
    )

    # ========================================================
    # 5. 一致性过滤
    # ========================================================

    start = time.perf_counter()

    llm_result = filter_llm_result(
        normalized_case,
        raw_llm_result
    )

    print(
        f"[耗时] 补全候选一致性过滤："
        f"{time.perf_counter() - start:.3f}秒"
    )

    print(
        "[过滤后真实缺失] "
        f"功能："
        f"{len(llm_result.get('missingFunctions', []))}"
        f"，关系："
        f"{len(llm_result.get('missingRelations', []))}"
    )

    # ========================================================
    # 6. 输出证据来源
    # ========================================================

    for function in llm_result.get(
        "missingFunctions",
        []
    ):
        print(
            "[补全功能] "
            f"{function.get('id', '')} "
            f"{function.get('name', '')} | "
            f"来源={function.get('evidenceType', '')} | "
            f"confidence={function.get('confidence', 0)}"
        )

    for relation in llm_result.get(
        "missingRelations",
        []
    ):
        print(
            "[补全关系] "
            f"{relation.get('source', '')}"
            f" -> "
            f"{relation.get('target', '')} | "
            f"type={relation.get('relation_type', '')} | "
            f"来源={relation.get('evidenceType', '')} | "
            f"confidence={relation.get('confidence', 0)}"
        )

    # ========================================================
    # 7. AI初步补全模型
    # ========================================================

    completion_result = (
        build_completion_result(
            normalized_case,
            llm_result
        )
    )

    total_time = (
        time.perf_counter()
        - total_start_time
    )

    print(
        f"[耗时] 功能补全总耗时："
        f"{total_time:.3f}秒"
    )

    print(
        f"[结果] AI补全后功能数量："
        f"{len(completion_result.get('functions', []))}"
    )

    print(
        f"[结果] AI补全后关系数量："
        f"{len(completion_result.get('relations', []))}"
    )

    return {
        # RAG历史证据
        "retrieval": retrieved,

        # 过滤后的真正缺失
        "llm_result": llm_result,

        # Qwen未经一致性过滤的原始候选
        "raw_llm_result": raw_llm_result,

        # 当前设计 + AI缺失项
        "completion_result": completion_result
    }
