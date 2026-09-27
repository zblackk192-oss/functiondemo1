"""
模拟用户确认
"""
def confirm_completion(llm_result):

    print("\n===== 大模型补全建议 =====")

    print(llm_result)


    choice = input(
        "\n是否接受补全结果?(y/n): "
    )


    if choice.lower()=="y":

        return True

    else:

        return False