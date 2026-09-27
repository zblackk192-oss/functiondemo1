"""
离线构建汽车系统案例向量知识库。

运行：

python build_knowledge_base.py

作用：

历史案例
    ↓
功能签名构造
    ↓
BGE向量化
    ↓
FAISS索引
    ↓
保存faiss.index
    +
保存metadata.json
"""


import config


from utils.json_utils import (
    load_history_cases
)


from service.retrieval_service import (
    build_case_vector_database
)


def main():

    print("=" * 60)

    print(
        "开始离线构建汽车系统案例向量知识库"
    )

    print("=" * 60)


    # ==================================================
    # 1. 加载历史案例
    # ==================================================

    print(
        "\n[1/3] 加载历史案例..."
    )


    history_cases = load_history_cases(
        config.HISTORY_CASE_DIR
    )


    print(
        f"已加载历史案例："
        f"{len(history_cases)} 个"
    )


    # ==================================================
    # 2. 构建向量数据库
    # ==================================================

    print(
        "\n[2/3] 构建FAISS向量数据库..."
    )


    db = build_case_vector_database(
        history_cases
    )


    print(
        f"已建立向量数量："
        f"{db.index.ntotal}"
    )


    print(
        f"向量维度："
        f"{db.index.d}"
    )


    # ==================================================
    # 3. 保存数据库
    # ==================================================

    print(
        "\n[3/3] 保存向量数据库..."
    )


    db.save(

        config.FAISS_INDEX_PATH,

        config.FAISS_METADATA_PATH
    )


    print(
        "\n离线知识库构建完成"
    )


    print(
        f"FAISS索引："
        f"{config.FAISS_INDEX_PATH}"
    )


    print(
        f"Metadata："
        f"{config.FAISS_METADATA_PATH}"
    )


    print("=" * 60)


if __name__ == "__main__":

    main()