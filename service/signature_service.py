"""
功能签名构造服务

用于RAG检索。

当前签名包含：

action
object
effect
trigger
condition
inputs
outputs
preconditions
postconditions
scenario
constraint
"""


def _to_text(value):

    """
    将字段统一转换成字符串。
    """

    if value is None:

        return ""


    if isinstance(value, list):

        return " ".join(
            str(item)
            for item in value
        )


    return str(value)


def build_signature(function: dict) -> str:

    """
    根据功能点构造语义签名。
    """

    parts = [

        _to_text(
            function.get("action", "")
        ),

        _to_text(
            function.get("object", "")
        ),

        _to_text(
            function.get("effect", "")
        ),

        _to_text(
            function.get("trigger", "")
        ),

        _to_text(
            function.get("condition", "")
        ),

        _to_text(
            function.get("inputs", [])
        ),

        _to_text(
            function.get("outputs", [])
        ),

        _to_text(
            function.get("preconditions", [])
        ),

        _to_text(
            function.get("postconditions", [])
        ),

        _to_text(
            function.get("scenario", "")
        ),

        _to_text(
            function.get("constraint", "")
        )
    ]


    signature = " ".join(
        part
        for part in parts
        if part
    )


    return signature.strip()