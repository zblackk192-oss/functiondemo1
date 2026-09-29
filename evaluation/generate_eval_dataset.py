import os
import json
import copy


# ============================================================
# 路径配置
# ============================================================

HISTORY_CASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history_cases")
EVAL_CASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "eval_cases")


# ============================================================
# JSON读取
# ============================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# JSON保存
# ============================================================

def save_json(data, path):

    os.makedirs(
        os.path.dirname(path),
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


# ============================================================
# 统一案例格式
#
# 兼容：
#
# {
#   "caseId": ...
# }
#
# 或：
#
# [
#   {
#      "caseId": ...
#   }
# ]
# ============================================================

def normalize_cases(data):

    if isinstance(data, list):

        return data

    if isinstance(data, dict):

        return [data]

    raise ValueError(
        "JSON格式错误：必须是对象或对象数组"
    )


# ============================================================
# 构造评价案例
#
# 策略：
#
# 从完整案例中：
#
# 保留第一个功能
# 删除后续功能
#
# 删除与缺失功能相关的关系
#
# Ground Truth保存被删除的功能和关系
# ============================================================

def build_eval_case(
        case,
        eval_id
):

    functions = case.get(
        "functions",
        []
    )

    relations = case.get(
        "relations",
        []
    )

    # 至少需要2个功能才能构造补全任务
    if len(functions) < 2:

        return None

    # --------------------------------------------------------
    # 当前输入
    #
    # 这里默认保留第一个功能
    # 后续可以扩展为随机遮蔽
    # --------------------------------------------------------

    existing_functions = [
        copy.deepcopy(
            functions[0]
        )
    ]

    missing_functions = [
        copy.deepcopy(
            f
        )
        for f in functions[1:]
    ]

    existing_ids = {
        f["id"]
        for f in existing_functions
    }

    missing_ids = {
        f["id"]
        for f in missing_functions
    }

    # --------------------------------------------------------
    # 当前已有关系
    #
    # 两端都属于已有功能的关系才能保留
    # --------------------------------------------------------

    existing_relations = []

    missing_relations = []

    for relation in relations:

        source = relation.get(
            "source"
        )

        target = relation.get(
            "target"
        )

        if (
            source in existing_ids
            and
            target in existing_ids
        ):

            existing_relations.append(
                copy.deepcopy(
                    relation
                )
            )

        elif (
            source in missing_ids
            or
            target in missing_ids
        ):

            missing_relations.append(
                copy.deepcopy(
                    relation
                )
            )

    # --------------------------------------------------------
    # 构造评价输入
    # --------------------------------------------------------

    eval_input = {

        "caseId":
            f"{case.get('caseId', eval_id)}_EVAL",

        "projectName":
            case.get(
                "projectName",
                ""
            ),

        "functions":
            existing_functions,

        "relations":
            existing_relations
    }

    # --------------------------------------------------------
    # 构造Ground Truth
    # --------------------------------------------------------

    ground_truth = {

        "sourceCaseId":
            case.get(
                "caseId",
                ""
            ),

        "missingFunctions":
            missing_functions,

        "missingRelations":
            missing_relations
    }

    # --------------------------------------------------------
    # 最终评价文件
    # --------------------------------------------------------

    result = {

        "evalId":
            eval_id,

        "input":
            eval_input,

        "groundTruth":
            ground_truth

    }

    return result


# ============================================================
# 主函数
# ============================================================

def main():

    os.makedirs(
        EVAL_CASE_DIR,
        exist_ok=True
    )

    eval_index = 1

    # --------------------------------------------------------
    # 遍历history_cases目录
    # --------------------------------------------------------

    files = sorted(
        os.listdir(
            HISTORY_CASE_DIR
        )
    )

    for filename in files:

        if not filename.endswith(
            ".json"
        ):

            continue

        path = os.path.join(
            HISTORY_CASE_DIR,
            filename
        )

        print(
            f"\n读取历史案例：{filename}"
        )

        data = load_json(
            path
        )

        cases = normalize_cases(
            data
        )

        for case in cases:

            eval_id = (
                f"EVAL{eval_index:03d}"
            )

            eval_case = build_eval_case(
                case,
                eval_id
            )

            if eval_case is None:

                print(
                    f"跳过 {eval_id}："
                    "功能数量不足2个"
                )

                continue

            output_path = os.path.join(
                EVAL_CASE_DIR,
                f"eval_case_{eval_index:03d}.json"
            )

            save_json(
                eval_case,
                output_path
            )

            print(
                f"生成评价案例："
                f"{output_path}"
            )

            eval_index += 1

    print(
        "\n================================"
    )

    print(
        f"评价数据集生成完成，共{eval_index - 1}个案例"
    )

    print(
        "================================"
    )


if __name__ == "__main__":

    main()
