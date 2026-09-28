import os

from dotenv import load_dotenv


# ==================================================
# 加载.env文件
# ==================================================

load_dotenv()


def env_to_bool(
    name,
    default=False
):

    value = os.getenv(
        name
    )

    if value is None:

        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


# ==================================================
# 历史案例
# ==================================================

HISTORY_CASE_DIR = "data/history_cases"


# ==================================================
# 当前待补全案例
# ==================================================

# "api"  -> 从上游接口获取
# "file" -> 从本地JSON获取
CURRENT_CASE_SOURCE = os.getenv(
    "CURRENT_CASE_SOURCE",
    "api"
)

CURRENT_CASE_PATH = (
    "data/current_case.json"
)

CURRENT_CASE_API_URL = os.getenv(
    "CURRENT_CASE_API_URL",
    (
        "https://function-fusion-api.onrender.com"
        "/api/v1/function-fusion/fuse"
    )
)

CURRENT_CASE_API_PAYLOAD = {
    "function_point_sets": [],
    "relations": []
}


# ==================================================
# 本地输出
# ==================================================

OUTPUT_PATH = "output/result.json"

SEMANTIC_GRAPH_PATH = (
    "output/semantic_graph.json"
)


# ==================================================
# 结果发布API
# ==================================================

# 是否把补全结果推送到结果API
RESULT_API_ENABLED = env_to_bool(
    "RESULT_API_ENABLED",
    True
)

# 推送失败时是否让当前任务直接失败
RESULT_API_REQUIRED = env_to_bool(
    "RESULT_API_REQUIRED",
    True
)

# 结果API的接收地址
RESULT_API_URL = os.getenv(
    "RESULT_API_URL",
    "http://127.0.0.1:8001/api/v1/results"
)

# 生产者与结果API之间的共享Token
RESULT_API_TOKEN = os.getenv(
    "RESULT_API_TOKEN",
    ""
)

# 请求超时时间
RESULT_API_TIMEOUT = float(
    os.getenv(
        "RESULT_API_TIMEOUT",
        "30"
    )
)


# ==================================================
# Qwen配置
# ==================================================

QWEN_API_KEY = os.getenv(
    "QWEN_API_KEY"
)

QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL"
)

QWEN_MODEL = "qwen3.8-max"


# ==================================================
# RAG向量知识库
# ==================================================

VECTOR_DB_DIR = "data/vector_db"

FAISS_INDEX_PATH = (
    "data/vector_db/faiss.index"
)

FAISS_METADATA_PATH = (
    "data/vector_db/metadata.json"
)


# ==================================================
# BGE Embedding模型
# ==================================================

BGE_MODEL_PATH = (
    "model/bge-small-zh-v1_5"
)