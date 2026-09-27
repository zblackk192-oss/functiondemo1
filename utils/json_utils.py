import json
import os


# ==================================================
# 读取单个JSON
# ==================================================

def load_json(path):

    """
    读取单个JSON文件。
    """

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"JSON文件不存在：{path}"
        )


    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ==================================================
# 保存JSON
# ==================================================

def save_json(
    data,
    path
):

    """
    保存JSON文件。
    """

    directory = os.path.dirname(
        path
    )


    if directory:

        os.makedirs(
            directory,
            exist_ok=True
        )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==================================================
# 加载历史案例
# ==================================================

def load_history_cases(
    directory
):

    """
    读取历史案例目录下的所有JSON文件。
    """

    if not os.path.exists(directory):

        raise FileNotFoundError(
            f"历史案例目录不存在：{directory}"
        )


    history_cases = []


    for filename in os.listdir(
        directory
    ):

        if not filename.lower().endswith(
            ".json"
        ):

            continue


        file_path = os.path.join(
            directory,
            filename
        )


        try:

            data = load_json(
                file_path
            )


            # ------------------------------------------
            # 单个文件就是一个案例
            # ------------------------------------------

            if isinstance(
                data,
                dict
            ):

                history_cases.append(
                    data
                )


            # ------------------------------------------
            # 兼容案例数组
            # ------------------------------------------

            elif isinstance(
                data,
                list
            ):

                history_cases.extend(
                    data
                )


        except Exception as e:

            print(
                f"读取历史案例失败：{filename}"
            )

            print(
                f"错误信息：{e}"
            )


    return history_cases