"""
比较两个案例
"""


def compare_case(current_case, history_case):

    current_names = []

    for f in current_case["functions"]:
        current_names.append(
            f["name"]
        )

    missing_functions = []

    for f in history_case["functions"]:

        if f["name"] not in current_names:

            missing_functions.append(f)

    return missing_functions

def compare_relation(current_case, history_case):

    current_relation = []

    for r in current_case["relations"]:

        current_relation.append(
            (
                r["source"],
                r["target"],
                r["type"]
            )
        )

    missing_relation = []

    for r in history_case["relations"]:

        key = (
            r["source"],
            r["target"],
            r["type"]
        )

        if key not in current_relation:

            missing_relation.append(r)

    return missing_relation