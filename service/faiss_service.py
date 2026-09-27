import faiss
import numpy as np
import json
import os
import time


class FAISSIndex:

    def __init__(self, dimension):

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.data = []


    # ==================================================
    # 添加向量
    # ==================================================

    def add(
        self,
        vectors,
        metadata
    ):

        start_time = time.perf_counter()

        vectors = np.array(
            vectors
        ).astype(
            "float32"
        )

        self.index.add(
            vectors
        )

        self.data.extend(
            metadata
        )

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        print(
            f"[耗时] FAISS添加向量："
            f"{elapsed_time:.3f}秒"
        )


    # ==================================================
    # FAISS检索
    # ==================================================

    def search(
        self,
        query_vector,
        top_k=3
    ):

        start_time = time.perf_counter()

        query_vector = np.array(
            [query_vector]
        ).astype(
            "float32"
        )

        # 实际检索
        scores, indexes = self.index.search(
            query_vector,
            top_k
        )

        results = []

        for score, index in zip(
            scores[0],
            indexes[0]
        ):

            if index != -1:

                results.append(
                    {
                        "score": float(score),
                        "data": self.data[index]
                    }
                )

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        print(
            f"[耗时] FAISS Top-{top_k}检索："
            f"{elapsed_time:.3f}秒"
        )

        return results


    # ==================================================
    # 保存FAISS索引
    # ==================================================

    def save(
        self,
        index_path,
        metadata_path
    ):

        start_time = time.perf_counter()

        directory = os.path.dirname(
            index_path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        faiss.write_index(
            self.index,
            index_path
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=2
            )

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        print(
            f"[耗时] 保存FAISS索引："
            f"{elapsed_time:.3f}秒"
        )


    # ==================================================
    # 加载FAISS索引
    # ==================================================

    @classmethod
    def load(
        cls,
        index_path,
        metadata_path
    ):

        start_time = time.perf_counter()

        print(
            "\n开始加载FAISS向量知识库..."
        )

        index = faiss.read_index(
            index_path
        )

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        db = cls(
            index.d
        )

        db.index = index

        db.data = data

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        print(
            f"FAISS索引加载完成，"
            f"耗时：{elapsed_time:.3f}秒"
        )

        print(
            f"向量数量：{index.ntotal}"
        )

        print(
            f"向量维度：{index.d}"
        )

        print(
            f"Metadata数量：{len(data)}"
        )

        return db