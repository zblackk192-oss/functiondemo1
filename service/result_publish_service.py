from typing import Any, Dict

import requests

import config


EVENT_TEXT_FIELDS = (
    "actor",
    "action",
    "object",
    "effect",
    "trigger",
    "condition"
)

EVENT_LIST_FIELDS = (
    "inputs",
    "outputs",
    "preconditions",
    "postconditions"
)


def _normalize_list(value):

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _normalize_confidence(value):

    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0

    return max(
        0.0,
        min(
            1.0,
            confidence
        )
    )


def _build_function_point(
    function: Dict[str, Any],
    index: int
):

    if not isinstance(function, dict):
        function = {}

    function_id = str(
        function.get("id")
        or function.get("functionId")
        or f"F{index + 1:03d}"
    )

    event = {
        field: (
            ""
            if function.get(field) is None
            else str(function.get(field, ""))
        )
        for field in EVENT_TEXT_FIELDS
    }

    for field in EVENT_LIST_FIELDS:
        event[field] = _normalize_list(
            function.get(field, [])
        )

    return {
        "id": function_id,
        "name": (
            ""
            if function.get("name") is None
            else str(function.get("name", ""))
        ),
        "event": event
    }


def _build_relation(
    relation: Dict[str, Any],
    function_name_map: Dict[str, str]
):

    if not isinstance(relation, dict):
        relation = {}

    source = str(
        relation.get("source", "")
    ).strip()

    target = str(
        relation.get("target", "")
    ).strip()

    relation_type = str(
        relation.get("relation_type")
        or relation.get("type")
        or "dependency"
    ).strip()

    direction = str(
        relation.get("direction")
        or "source_to_target"
    ).strip()

    return {
        "source": source,
        "target": target,
        "source_name": str(
            relation.get("source_name")
            or function_name_map.get(source, "")
        ),
        "target_name": str(
            relation.get("target_name")
            or function_name_map.get(target, "")
        ),
        "relation_type": relation_type,
        "direction": direction,
        "confidence": _normalize_confidence(
            relation.get("confidence", 0.0)
        ),
        "evidence": (
            ""
            if relation.get("evidence") is None
            else str(relation.get("evidence", ""))
        )
    }


def build_published_payload(
    internal_result: Dict[str, Any],
    current_case: Dict[str, Any]
):
    """
    将内部可解释结果转换为下游标准载荷。

    internal_result中的retrieval、raw_llm_result、llm_result以及
    各类reason/historyEvidence不会进入published_result.json。
    """

    if not isinstance(internal_result, dict):
        raise ValueError("内部result必须是JSON对象")

    if not isinstance(current_case, dict):
        current_case = {}

    completion_result = internal_result.get(
        "completion_result",
        {}
    )

    if not isinstance(completion_result, dict):
        completion_result = {}

    functions = completion_result.get(
        "functions",
        []
    )

    relations = completion_result.get(
        "relations",
        []
    )

    if not isinstance(functions, list):
        functions = []

    if not isinstance(relations, list):
        relations = []

    function_points = [
        _build_function_point(function, index)
        for index, function in enumerate(functions)
        if isinstance(function, dict)
    ]

    function_name_map = {
        point["id"]: point["name"]
        for point in function_points
    }

    published_relations = [
        _build_relation(
            relation,
            function_name_map
        )
        for relation in relations
        if isinstance(relation, dict)
    ]

    request_id = (
        current_case.get("request_id")
        or current_case.get("caseId")
        or ""
    )

    return {
        "request_id": str(request_id),
        "status": str(
            current_case.get("status", "")
        ),
        "result": {
            "function_point_set": {
                "raw_text": str(
                    current_case.get("raw_text", "")
                    or ""
                ),
                "function_points": function_points,
                "summary": str(
                    current_case.get("summary", "")
                    or ""
                )
            },
            "relations": published_relations
        },
        "error": current_case.get("error")
    }


# ============================================================
# 执行结果推送
# ============================================================

def _send_result(
    result: Dict[str, Any]
):

    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "待发布的result必须是JSON对象"
        )

    api_url = (
        config.RESULT_API_URL
        or ""
    ).strip()

    if not api_url:

        raise RuntimeError(
            "未配置RESULT_API_URL"
        )

    try:

        response = requests.post(
            api_url,
            json=result,
            timeout=(
                config.RESULT_API_TIMEOUT
            )
        )

        response.raise_for_status()

    except requests.Timeout as e:

        raise RuntimeError(
            "向结果API推送数据超时："
            f"{api_url}"
        ) from e

    except requests.RequestException as e:

        response_body = ""

        if (
            e.response is not None
            and e.response.text
        ):

            response_body = (
                e.response.text[:500]
            )

        raise RuntimeError(
            "向结果API推送数据失败："
            f"{api_url}；"
            f"错误信息：{e}；"
            f"响应内容：{response_body}"
        ) from e

    try:

        response_data = response.json()

    except ValueError:

        response_data = {
            "status_code":
            response.status_code
        }

    return {
        "enabled": True,
        "success": True,
        "api_url": api_url,
        "response": response_data
    }


# ============================================================
# 对外发布函数
# ============================================================

def publish_result(
    result: Dict[str, Any],
    current_case: Dict[str, Any] = None
):

    if not config.RESULT_API_ENABLED:

        return {
            "enabled": False,
            "success": False,
            "message": "结果API推送已关闭"
        }

    try:

        published_payload = build_published_payload(
            result,
            current_case or {}
        )

        publish_status = _send_result(
            published_payload
        )

        print(
            "[结果发布] 推送成功"
        )

        result_id = (
            publish_status
            .get(
                "response",
                {}
            )
            .get(
                "result_id",
                ""
            )
        )

        if result_id:

            print(
                f"[结果发布] result_id："
                f"{result_id}"
            )

        return publish_status

    except Exception as e:

        print(
            f"[结果发布] 推送失败：{e}"
        )

        if config.RESULT_API_REQUIRED:

            raise

        return {
            "enabled": True,
            "success": False,
            "message": str(e)
        }
