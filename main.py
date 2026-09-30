import time


# ==================================================
# 程序启动计时
# ==================================================

PROGRAM_START_TIME = time.perf_counter()


import config

from utils.json_utils import (
    save_json
)

from service.current_case_service import (
    load_current_case
)

from service.completion_service import (
    completion,
    normalize_current_case
)

from service.user_confirm_service import (
    confirm_completion
)

from service.graph_service import (
    build_semantic_graph,
    save_semantic_graph
)

from service.result_publish_service import (
    publish_result
)

# ==================================================
# 主程序
# ==================================================

def main():

    main_start_time = time.perf_counter()

    print("\n")
    print("=" * 60)
    print("汽车系统功能点及关联关系补全Demo")
    print("=" * 60)

    # ==================================================
    # 1. 检查知识库API配置
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【1/8】检查知识库API配置")

    if not config.KNOWLEDGE_API_URL:
        raise RuntimeError(
            "未配置KNOWLEDGE_API_URL"
        )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"知识库API：{config.KNOWLEDGE_API_URL}\n"
        f"知识库Top-K：{config.KNOWLEDGE_API_TOP_K}\n"
        f"[耗时] 配置检查："
        f"{step_time:.3f}秒"
    )

    # ==================================================
    # 2. 读取当前设计输入
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【2/8】读取当前设计输入")

    current_case = load_current_case()

    normalized_case = normalize_current_case(
        current_case
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 读取并标准化当前案例："
        f"{step_time:.3f}秒"
    )

    print(
        f"当前设计案例："
        f"{normalized_case.get('caseId', 'CURRENT001')}"
    )

    print(
        f"当前功能数量："
        f"{len(normalized_case.get('functions', []))}"
    )

    print(
        f"当前关系数量："
        f"{len(normalized_case.get('relations', []))}"
    )

    # ==================================================
    # 3. 知识库API检索 + Qwen补全
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【3/8】知识库API检索 + Qwen补全")

    result = completion(
        current_case,
        k=config.KNOWLEDGE_API_TOP_K
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"\n[耗时] 【3/8】知识库检索+Qwen总耗时："
        f"{step_time:.3f}秒"
    )

    # ==================================================
    # 4. 获取Qwen结果
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【4/8】获取Qwen结果")

    llm_result = result.get(
        "llm_result",
        {}
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 获取Qwen结果："
        f"{step_time:.3f}秒"
    )

    print(
        f"Qwen补全功能："
        f"{len(llm_result.get('missingFunctions', []))}"
    )

    print(
        f"Qwen补全关系："
        f"{len(llm_result.get('missingRelations', []))}"
    )

    # ==================================================
    # 5. 保存AI原始结果
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【5/8】保存AI补全结果")

    save_json(
        result,
        config.OUTPUT_PATH
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 保存result.json："
        f"{step_time:.3f}秒"
    )

    # ==================================================
    # 6. 用户确认
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【6/8】用户确认")

    if not confirm_completion(
        llm_result
    ):

        step_time = (
            time.perf_counter()
            - step_start_time
        )

        print(
            f"[耗时] 用户确认阶段："
            f"{step_time:.3f}秒"
        )

        print(
            "\n用户拒绝补全"
        )

        return

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 用户确认阶段："
        f"{step_time:.3f}秒"
    )

    print(
        "\n用户确认Qwen补全建议"
    )

    # ==================================================
    # 发布已确认的补全结果
    # ==================================================

    print()
    print("正在向结果API发布补全结果")

    publish_status = publish_result(
        result,
        normalized_case
    )

    print(
        f"结果发布状态："
        f"{publish_status.get('success', False)}"
    )
    # ==================================================
    # 7. 获取最终标准化模型
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【7/8】获取最终标准化模型")

    completion_result = result.get(
        "completion_result",
        {
            "functions": [],
            "relations": []
        }
    )

    final_functions = completion_result.get(
        "functions",
        []
    )

    final_relations = completion_result.get(
        "relations",
        []
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 获取标准化结果："
        f"{step_time:.3f}秒"
    )

    print(
        f"[模型] 最终功能数量："
        f"{len(final_functions)}"
    )

    print(
        f"[模型] 最终关系数量："
        f"{len(final_relations)}"
    )

    # ==================================================
    # 8. 构建功能语义图
    # ==================================================

    step_start_time = time.perf_counter()

    print("\n")
    print("【8/8】构建功能语义图")

    # --------------------------------------------------
    # 当前已有功能
    # --------------------------------------------------

    current_functions = normalized_case.get(
        "functions",
        []
    )

    # --------------------------------------------------
    # AI新增功能
    # --------------------------------------------------

    missing_functions = llm_result.get(
        "missingFunctions",
        []
    )

    # --------------------------------------------------
    # 构建语义图
    # --------------------------------------------------

    graph = build_semantic_graph(

        current_functions=
        current_functions,

        missing_functions=
        missing_functions,

        missing_relations=
        final_relations
    )

    # --------------------------------------------------
    # 保存语义图
    # --------------------------------------------------

    save_semantic_graph(
        graph,
        config.SEMANTIC_GRAPH_PATH
    )

    step_time = (
        time.perf_counter()
        - step_start_time
    )

    print(
        f"[耗时] 构建并保存功能语义图："
        f"{step_time:.3f}秒"
    )

    print(
        "\n功能语义图生成完成："
    )

    print(
        config.SEMANTIC_GRAPH_PATH
    )

    print(
        f"语义图节点数量："
        f"{len(graph.get('nodes', []))}"
    )

    print(
        f"语义图关系数量："
        f"{len(graph.get('edges', []))}"
    )

    # ==================================================
    # 总耗时
    # ==================================================

    total_time = (
        time.perf_counter()
        - main_start_time
    )

    process_startup_time = (
        main_start_time
        - PROGRAM_START_TIME
    )

    print("\n")
    print("=" * 60)
    print("Demo运行完成")
    print("=" * 60)

    print(
        f"程序启动/模块加载阶段："
        f"{process_startup_time:.3f}秒"
    )

    print(
        f"main()执行阶段："
        f"{total_time:.3f}秒"
    )

    print(
        f"程序总耗时："
        f"{process_startup_time + total_time:.3f}秒"
    )

    print("=" * 60)


# ==================================================
# 程序入口
# ==================================================

if __name__ == "__main__":

    main()
