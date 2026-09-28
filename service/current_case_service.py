import requests

import config

from utils.json_utils import load_json


# ============================================================
# API请求超时时间
# ============================================================

API_TIMEOUT_SECONDS = 30


# ============================================================
# 从上游API获取当前案例
# ============================================================

def load_current_case_from_api():

    """
    调用上游多源融合接口，获取当前待补全案例。
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

        raise RuntimeError(
            "调用上游当前案例接口失败："
            f"{config.CURRENT_CASE_API_URL}；"
            f"错误信息：{e}"
        ) from e

    try:

        current_case = response.json()

    except ValueError as e:

        raise RuntimeError(
            "上游接口返回的内容不是有效JSON"
        ) from e

    if not isinstance(
        current_case,
        dict
    ):

        raise RuntimeError(
            "上游接口返回格式错误："
            "响应根节点必须是JSON对象"
        )

    if not isinstance(
        current_case.get(
            "functions"
        ),
        list
    ):

        raise RuntimeError(
            "上游接口返回格式错误："
            "functions字段必须是数组"
        )

    if not isinstance(
        current_case.get(
            "relations"
        ),
        list
    ):

        raise RuntimeError(
            "上游接口返回格式错误："
            "relations字段必须是数组"
        )

    return current_case


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

        return load_json(
            config.CURRENT_CASE_PATH
        )

    raise ValueError(
        "不支持的CURRENT_CASE_SOURCE："
        f"{config.CURRENT_CASE_SOURCE}；"
        "只允许使用api或file"
    )