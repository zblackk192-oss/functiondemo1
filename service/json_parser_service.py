import json
import re


def parse_llm_json(text):

    """
    将Qwen输出字符串解析为JSON
    """

    try:

        # 去除markdown代码块

        text = re.sub(
            r"```json|```",
            "",
            text
        ).strip()


        result = json.loads(text)


        return result


    except Exception as e:

        return {

            "error":
                "JSON解析失败",

            "raw":

                text,

            "exception":

                str(e)
        }