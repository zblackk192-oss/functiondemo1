import os
import time

from sentence_transformers import SentenceTransformer

import config


# ==================================================
# BGE模型路径
# ==================================================

MODEL_PATH = config.BGE_MODEL_PATH


# ==================================================
# 检查模型是否存在
# ==================================================

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        f"BGE模型不存在：{MODEL_PATH}\n"
        "请先下载BAAI/bge-small-zh-v1.5到该目录。"
    )


# ==================================================
# 加载BGE模型
# ==================================================

print("=" * 60)
print("开始加载本地BGE模型")
print(f"模型路径：{MODEL_PATH}")
print("=" * 60)

_embedding_start_time = time.perf_counter()


model = SentenceTransformer(
    MODEL_PATH
)


_embedding_load_time = (
    time.perf_counter()
    - _embedding_start_time
)


print(
    f"BGE模型加载完成，耗时："
    f"{_embedding_load_time:.3f}秒"
)

print("=" * 60)


# ==================================================
# 文本转向量
# ==================================================

def encode_text(text):

    start_time = time.perf_counter()

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    elapsed_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[耗时] BGE文本编码："
        f"{elapsed_time:.3f}秒"
    )

    return vector