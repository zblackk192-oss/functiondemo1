import os
import json
import sys

# ============================================================
# 将项目根目录加入Python路径
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)


from service.retrieval_service import (
    build_case_vector_database,
    retrieve_top_k_cases
)

from service.completion_service import completion

from utils.json_utils import load_json


# ============================================================
# 路径配置
# ============================================================

HISTORY_CASE_DIR = os.path.join(
    PROJECT_ROOT,
    "data",
    "history_cases"
)

EVAL_CASE_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "eval_cases"
)

RESULT_PATH = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "evaluation_result.json"
)


# ============================================================
# 参数
# ============================================================

TOP_K_LIST = [1, 2, 3]


# ============================================================
# 读取历史案例
# ============================================================

def load_history_cases():

    cases = []

    for filename in sorted(
        os.listdir(HISTORY_CASE_DIR)
    ):

        if not filename.endswith(
            ".json"
        ):
            continue

        path = os.path.join(
            HISTORY_CASE_DIR,
            filename
        )

        case = load_json(path)

        cases.append({
            "filename": filename,
            "case": case
        })

    return cases


# ============================================================
# 读取评价案例
# ============================================================

def load_eval_cases():

    cases = []

    for filename in sorted(
        os.listdir(EVAL_CASE_DIR)
    ):

        if not filename.endswith(
            ".json"
        ):
            continue

        path = os.path.join(
            EVAL_CASE_DIR,
            filename
        )

        case = load_json(path)

        cases.append({
            "filename": filename,
            "case": case
        })

    return cases


# ============================================================
# 获取评价案例对应的原始case
# ============================================================

def get_source_case_name(eval_case):

    # 推荐格式：
    #
    # "sourceCaseId": "paper_case_01"

    source_case = eval_case.get(
        "sourceCaseId"
    )

    if source_case:
        return source_case + ".json"

    # 如果没有sourceCaseId，
    # 则根据eval_case编号自动映射

    eval_id = eval_case.get(
        "evalId",
        ""
    )

    if eval_id:

        number = eval_id.replace(
            "EVAL",
            ""
        )

        if number.isdigit():

            return (
                f"paper_case_"
                f"{int(number):02d}.json"
            )

    return None


# ============================================================
# Leave-One-Case-Out
# ============================================================

def build_loco_history(
    all_history_cases,
    excluded_filename
):

    history_cases = []

    for item in all_history_cases:

        if (
            item["filename"]
            == excluded_filename
        ):
            continue

        history_cases.append(
            item["case"]
        )

    return history_cases


# ============================================================
# 计算检索相关性
# ============================================================

def evaluate_retrieval(
    retrieved,
    ground_truth_functions
):

    if not retrieved:
        return {
            "hit_at_k": 0,
            "max_score": 0,
            "mean_score": 0
        }

    scores = []

    hit = 0

    ground_truth_names = set()

    for function in ground_truth_functions:

        name = function.get(
            "name",
            ""
        )

        if name:
            ground_truth_names.add(
                name
            )

    for item in retrieved:

        score = item.get(
            "score",
            0
        )

        scores.append(
            score
        )

        data = item.get(
            "data",
            {}
        )

        function = data.get(
            "function",
            {}
        )

        function_name = function.get(
            "name",
            ""
        )

        if (
            function_name
            in ground_truth_names
        ):

            hit = 1

    return {

        "hit_at_k": hit,

        "max_score": max(
            scores
        ) if scores else 0,

        "mean_score": (
            sum(scores)
            / len(scores)
            if scores
            else 0
        )
    }


# ============================================================
# 功能补全准确率
# ============================================================

def evaluate_completion(
    predicted_functions,
    ground_truth_functions
):

    ground_truth_names = set()

    for function in ground_truth_functions:

        name = function.get(
            "name",
            ""
        )

        if name:
            ground_truth_names.add(
                name
            )

    predicted_names = set()

    for function in predicted_functions:

        name = function.get(
            "name",
            ""
        )

        if name:
            predicted_names.add(
                name
            )

    if not ground_truth_names:

        return {
            "precision": 0,
            "recall": 0,
            "f1": 0
        }

    true_positive = len(
        predicted_names
        & ground_truth_names
    )

    precision = (
        true_positive
        / len(predicted_names)
        if predicted_names
        else 0
    )

    recall = (
        true_positive
        / len(ground_truth_names)
    )

    if (
        precision + recall
        == 0
    ):

        f1 = 0

    else:

        f1 = (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
        )

    return {

        "precision": precision,

        "recall": recall,

        "f1": f1
    }


# ============================================================
# 单个K进行评价
# ============================================================

def evaluate_one_case(
    eval_case,
    history_cases,
    k
):

    input_case = eval_case.get(
        "inputCase",
        eval_case
    )

    ground_truth = eval_case.get(
        "groundTruth",
        {}
    )

    ground_truth_functions = (
        ground_truth.get(
            "functions",
            []
        )
    )

    # --------------------------------------------------------
    # 建立LOCO历史案例库
    # --------------------------------------------------------

    source_case_name = (
        get_source_case_name(
            eval_case
        )
    )

    loco_history = (
        build_loco_history(
            history_cases,
            source_case_name
        )
    )

    # --------------------------------------------------------
    # 建立临时FAISS
    # --------------------------------------------------------

    db = build_case_vector_database(
        loco_history
    )

    # --------------------------------------------------------
    # RAG检索
    # --------------------------------------------------------

    retrieved = retrieve_top_k_cases(
        input_case,
        db,
        k=k
    )

    # --------------------------------------------------------
    # 检索相关性评价
    # --------------------------------------------------------

    retrieval_metric = (
        evaluate_retrieval(
            retrieved,
            ground_truth_functions
        )
    )

    # --------------------------------------------------------
    # 大模型补全
    # --------------------------------------------------------

    result = completion(
        input_case,
        loco_history
    )

    completion_result = result.get(
        "completion_result",
        {}
    )

    predicted_functions = (
        completion_result.get(
            "functions",
            []
        )
    )

    # --------------------------------------------------------
    # 功能补全准确率
    # --------------------------------------------------------

    completion_metric = (
        evaluate_completion(
            predicted_functions,
            ground_truth_functions
        )
    )

    return {

        "evalCase":
            eval_case.get(
                "evalId",
                ""
            ),

        "sourceCase":
            source_case_name,

        "k":
            k,

        "historyCases": [
            item["caseId"]
            for item in loco_history
        ],

        "retrieval": {

            "hitAtK":
                retrieval_metric[
                    "hit_at_k"
                ],

            "maxScore":
                retrieval_metric[
                    "max_score"
                ],

            "meanScore":
                retrieval_metric[
                    "mean_score"
                ]
        },

        "completion": {

            "precision":
                completion_metric[
                    "precision"
                ],

            "recall":
                completion_metric[
                    "recall"
                ],

            "f1":
                completion_metric[
                    "f1"
                ]
        },

        "retrievedResults":
            retrieved,

        "predictedFunctions":
            predicted_functions
    }


# ============================================================
# 主评价程序
# ============================================================

def main():

    print("=" * 70)
    print("Leave-One-Case-Out 功能补全评价")
    print("=" * 70)

    history_cases = (
        load_history_cases()
    )

    eval_cases = (
        load_eval_cases()
    )

    print(
        f"历史案例数量："
        f"{len(history_cases)}"
    )

    print(
        f"评价案例数量："
        f"{len(eval_cases)}"
    )

    all_results = []

    # ========================================================
    # 对不同K分别评价
    # ========================================================

    for k in TOP_K_LIST:

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"当前Top-K = {k}"
        )

        print(
            "-" * 70
        )

        k_results = []

        for item in eval_cases:

            eval_case = item["case"]

            print(
                f"\n评价："
                f"{item['filename']}"
            )

            result = evaluate_one_case(
                eval_case,
                history_cases,
                k
            )

            k_results.append(
                result
            )

            print(
                f"  排除："
                f"{result['sourceCase']}"
            )

            print(
                f"  Hit@{k}："
                f"{result['retrieval']['hitAtK']}"
            )

            print(
                f"  最大相似度："
                f"{result['retrieval']['maxScore']:.4f}"
            )

            print(
                f"  补全Precision："
                f"{result['completion']['precision']:.4f}"
            )

            print(
                f"  补全Recall："
                f"{result['completion']['recall']:.4f}"
            )

            print(
                f"  补全F1："
                f"{result['completion']['f1']:.4f}"
            )

        # ====================================================
        # 当前K的平均结果
        # ====================================================

        if k_results:

            avg_hit = (
                sum(
                    r["retrieval"]["hitAtK"]
                    for r in k_results
                )
                / len(k_results)
            )

            avg_score = (
                sum(
                    r["retrieval"]["maxScore"]
                    for r in k_results
                )
                / len(k_results)
            )

            avg_precision = (
                sum(
                    r["completion"]["precision"]
                    for r in k_results
                )
                / len(k_results)
            )

            avg_recall = (
                sum(
                    r["completion"]["recall"]
                    for r in k_results
                )
                / len(k_results)
            )

            avg_f1 = (
                sum(
                    r["completion"]["f1"]
                    for r in k_results
                )
                / len(k_results)
            )

        else:

            avg_hit = 0
            avg_score = 0
            avg_precision = 0
            avg_recall = 0
            avg_f1 = 0

        all_results.append({

            "k": k,

            "cases":
                k_results,

            "average": {

                "hitAtK":
                    avg_hit,

                "maxScore":
                    avg_score,

                "precision":
                    avg_precision,

                "recall":
                    avg_recall,

                "f1":
                    avg_f1
            }
        })

        print(
            "\n当前K平均结果："
        )

        print(
            f"  Hit@{k}: "
            f"{avg_hit:.4f}"
        )

        print(
            f"  MaxScore: "
            f"{avg_score:.4f}"
        )

        print(
            f"  Precision: "
            f"{avg_precision:.4f}"
        )

        print(
            f"  Recall: "
            f"{avg_recall:.4f}"
        )

        print(
            f"  F1: "
            f"{avg_f1:.4f}"
        )

    # ========================================================
    # 保存结果
    # ========================================================

    with open(
        RESULT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "评价完成"
    )

    print(
        f"结果保存："
        f"{RESULT_PATH}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()