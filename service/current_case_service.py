import json

import requests

import config

from utils.json_utils import load_json


# ============================================================
# API请求超时时间
# ============================================================

API_TIMEOUT_SECONDS = 30


# ============================================================
# 校验JSON对象
# ============================================================

def require_dict(
    value,
    field_name
):

    if not isinstance(
        value,
        dict
    ):

        raise RuntimeError(
            "上游接口返回格式错误："
            f"{field_name}必须是JSON对象"
        )

    return value


# ============================================================
# 校验JSON数组
# ============================================================

def require_list(
    value,
    field_name
):

    if not isinstance(
        value,
        list
    ):

        raise RuntimeError(
            "上游接口返回格式错误："
            f"{field_name}必须是数组"
        )

    return value


# ============================================================
# 转换单个功能点
# ============================================================

def convert_function_point(
    function_point,
    index
):

    require_dict(
        function_point,
        (
            "result.function_point_set."
            f"function_points[{index}]"
        )
    )

    event = require_dict(
        function_point.get(
            "event"
        ),
        (
            "result.function_point_set."
            f"function_points[{index}].event"
        )
    )

    function_id = str(
        function_point.get(
            "id"
        )
        or event.get(
            "functionId"
        )
        or f"F{index + 1:03d}"
    )

    function_name = str(
        function_point.get(
            "name"
        )
        or event.get(
            "name"
        )
        or ""
    )

    # 复制event中的全部字段，包括actor、
    # action、object、effect等字段
    function = dict(
        event
    )

    # 转换成项目内部使用的功能字段
    function["id"] = function_id
    function["functionId"] = function_id
    function["name"] = function_name

    return function


# ============================================================
# 转换单个事件
# ============================================================

def convert_event(
    function_point,
    function
):

    event = dict(
        function_point.get(
            "event",
            {}
        )
    )

    event["functionId"] = function.get(
        "functionId",
        ""
    )

    event["name"] = function.get(
        "name",
        ""
    )

    return event


# ============================================================
# 转换单个关系
# ============================================================

def convert_relation(
    relation,
    index
):

    require_dict(
        relation,
        f"result.relations[{index}]"
    )

    source = relation.get(
        "source"
    )

    target = relation.get(
        "target"
    )

    if source is None or not str(source).strip():

        raise RuntimeError(
            "上游接口返回格式错误："
            f"result.relations[{index}].source不能为空"
        )

    if target is None or not str(target).strip():

        raise RuntimeError(
            "上游接口返回格式错误："
            f"result.relations[{index}].target不能为空"
        )

    converted_relation = dict(
        relation
    )

    converted_relation["source"] = str(
        source
    ).strip()

    converted_relation["target"] = str(
        target
    ).strip()

    # 项目内部使用type；
    # 新接口使用relation_type
    converted_relation["type"] = (
        relation.get(
            "relation_type"
        )
        or relation.get(
            "type"
        )
        or "dependency"
    )

    return converted_relation


# ============================================================
# 转换上游HTTP 200响应
# ============================================================

def convert_api_response(
    response_data
):

    require_dict(
        response_data,
        "响应根节点"
    )

    required_fields = [
        "request_id",
        "status",
        "result",
        "error"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in response_data
    ]

    if missing_fields:

        raise RuntimeError(
            "上游接口返回格式错误："
            "响应缺少字段："
            + ", ".join(
                missing_fields
            )
        )

    error = response_data.get(
        "error"
    )

    if error is not None:

        raise RuntimeError(
            "上游接口返回业务错误："
            + json.dumps(
                error,
                ensure_ascii=False
            )
        )

    result = require_dict(
        response_data.get(
            "result"
        ),
        "result"
    )

    function_point_set = require_dict(
        result.get(
            "function_point_set"
        ),
        "result.function_point_set"
    )

    function_points = require_list(
        function_point_set.get(
            "function_points"
        ),
        (
            "result.function_point_set."
            "function_points"
        )
    )

    raw_relations = require_list(
        result.get(
            "relations"
        ),
        "result.relations"
    )

    functions = []
    events = []

    for index, function_point in enumerate(
        function_points
    ):

        function = convert_function_point(
            function_point,
            index
        )

        functions.append(
            function
        )

        events.append(
            convert_event(
                function_point,
                function
            )
        )

    relations = []

    for index, relation in enumerate(
        raw_relations
    ):

        relations.append(
            convert_relation(
                relation,
                index
            )
        )

    request_id = response_data.get(
        "request_id",
        ""
    )

    raw_text = function_point_set.get(
        "raw_text",
        ""
    )

    summary = function_point_set.get(
        "summary",
        ""
    )

    return {
        # 项目内部字段
        "caseId": (
            str(request_id)
            if request_id
            else "CURRENT001"
        ),
        "projectName": "",
        "raw_text": (
            ""
            if raw_text is None
            else str(raw_text)
        ),
        "function_points": function_points,
        "events": events,
        "functions": functions,
        "relations": relations,

        # 保留上游响应信息
        "request_id": request_id,
        "status": response_data.get(
            "status",
            ""
        ),
        "summary": (
            ""
            if summary is None
            else str(summary)
        ),
        "error": error
    }


# ============================================================
# 从上游API获取当前案例
# ============================================================

def load_current_case_from_api():

    """
    调用上游多源融合接口，获取当前待补全案例。

    上游接口应返回HTTP 200，响应结构为：

    {
        "request_id": "",
        "status": "",
        "result": {
            "function_point_set": {
                "raw_text": "",
                "function_points": [],
                "summary": ""
            },
            "relations": []
        },
        "error": null
    }
    """

    try:

        response = requests.post(
            config.CURRENT_CASE_API_URL,
            json=config.CURRENT_CASE_API_PAYLOAD,
            timeout=API_TIMEOUT_SECONDS
        )

        response.raise_for_status()

    except requests.Timeout as e:

        raise RuntimeError(
            "获取当前案例超时："
            f"{config.CURRENT_CASE_API_URL}"
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
            "调用上游当前案例接口失败："
            f"{config.CURRENT_CASE_API_URL}；"
            f"错误信息：{e}；"
            f"响应内容：{response_body}"
        ) from e

    if response.status_code != 200:

        raise RuntimeError(
            "上游接口返回状态码错误："
            "期望HTTP 200，"
            f"实际为HTTP {response.status_code}"
        )

    try:

        response_data = response.json()

    except ValueError as e:

        raise RuntimeError(
            "上游接口返回的内容不是有效JSON"
        ) from e

    return convert_api_response(
        response_data
    )


# ============================================================
# 加载当前案例
# ============================================================

def load_current_case():

    source = str(
        config.CURRENT_CASE_SOURCE
    ).strip().lower()

    print(
        f"[当前案例] 输入来源：{source}"
    )

    if source == "api":

        print(
            f"[当前案例] API地址："
            f"{config.CURRENT_CASE_API_URL}"
        )

        return load_current_case_from_api()

    if source == "file":

        print(
            f"[当前案例] 文件路径："
            f"{config.CURRENT_CASE_PATH}"
        )

        # 本地文件继续使用项目原有的内部格式，
        # 不要求增加HTTP响应外层结构
        return load_json(
            config.CURRENT_CASE_PATH
        )

    raise ValueError(
        "不支持的CURRENT_CASE_SOURCE："
        f"{config.CURRENT_CASE_SOURCE}；"
        "只允许使用api或file"
    )