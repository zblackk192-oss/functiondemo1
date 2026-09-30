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

# 是否向结果API推送补全结果
RESULT_API_ENABLED = env_to_bool(
    "RESULT_API_ENABLED",
    True
)

# 推送失败时是否让补全请求失败
RESULT_API_REQUIRED = env_to_bool(
    "RESULT_API_REQUIRED",
    True
)

# 结果API的接收地址
RESULT_API_URL = os.getenv(
    "RESULT_API_URL",
    "http://127.0.0.1:8001/api/v1/results"
)

# 结果API请求超时时间
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

QWEN_API_TIMEOUT = float(
    os.getenv(
        "QWEN_API_TIMEOUT",
        "120"
    )
)

QWEN_MAX_RETRIES = int(
    os.getenv(
        "QWEN_MAX_RETRIES",
        "0"
    )
)

QWEN_EMPTY_RESULT_RECHECK_ENABLED = env_to_bool(
    "QWEN_EMPTY_RESULT_RECHECK_ENABLED",
    False
)


# ==================================================
# 知识库查询API
# ==================================================

KNOWLEDGE_API_URL = os.getenv(
    "KNOWLEDGE_API_URL",
    ""
).strip()

KNOWLEDGE_API_TOKEN = os.getenv(
    "KNOWLEDGE_API_TOKEN",
    ""
)

KNOWLEDGE_API_TIMEOUT = float(
    os.getenv(
        "KNOWLEDGE_API_TIMEOUT",
        "30"
    )
)

KNOWLEDGE_API_TOP_K = int(
    os.getenv(
        "KNOWLEDGE_API_TOP_K",
        "10"
    )
)

KNOWLEDGE_API_ARCHITECTURE_ID = os.getenv(
    "KNOWLEDGE_API_ARCHITECTURE_ID",
    ""
)

KNOWLEDGE_API_VIEW_TYPE = os.getenv(
    "KNOWLEDGE_API_VIEW_TYPE",
    ""
)

KNOWLEDGE_API_SUBGRAPH_ID = os.getenv(
    "KNOWLEDGE_API_SUBGRAPH_ID",
    ""
)

KNOWLEDGE_API_FUNCTION = os.getenv(
    "KNOWLEDGE_API_FUNCTION",
    ""
)

KNOWLEDGE_API_TAGS = [
    item.strip()
    for item in os.getenv(
        "KNOWLEDGE_API_TAGS",
        ""
    ).split(",")
    if item.strip()
]

KNOWLEDGE_API_COMPONENT_CATEGORY = os.getenv(
    "KNOWLEDGE_API_COMPONENT_CATEGORY",
    ""
)

KNOWLEDGE_API_MAX_QUERY_CHARS = int(
    os.getenv(
        "KNOWLEDGE_API_MAX_QUERY_CHARS",
        "4000"
    )
)
