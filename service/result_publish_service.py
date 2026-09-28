from typing import Any, Dict

import requests

import config


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
    result: Dict[str, Any]
):

    if not config.RESULT_API_ENABLED:

        return {
            "enabled": False,
            "success": False,
            "message": "结果API推送已关闭"
        }

    try:

        publish_status = _send_result(
            result
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