import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


# ==================================================
# 历史案例
# ==================================================

HISTORY_CASE_DIR = "data/history_cases"


# ==================================================
# 当前待补全案例
# ==================================================

# 输入来源：
# "api"  -> 从上游接口获取
# "file" -> 从本地 JSON 获取
CURRENT_CASE_SOURCE = os.getenv("CURRENT_CASE_SOURCE", "api")

# 本地文件输入（备用）
CURRENT_CASE_PATH = "data/current_case.json"

# 上游多源融合接口
CURRENT_CASE_API_URL = os.getenv(
    "CURRENT_CASE_API_URL",
    "https://function-fusion-api.onrender.com/api/v1/function-fusion/fuse"
)

# 调用上游接口时使用的请求体
CURRENT_CASE_API_PAYLOAD = {
    "function_point_sets": [],
    "relations": []
}


# ==================================================
# 输出
# ==================================================

OUTPUT_PATH = "output/result.json"

SEMANTIC_GRAPH_PATH = "output/semantic_graph.json"


# ==================================================
# Qwen 配置
# ==================================================

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")

QWEN_MODEL = "qwen3.8-max"


# ==================================================
# RAG 向量知识库
# ==================================================

VECTOR_DB_DIR = "data/vector_db"

FAISS_INDEX_PATH = "data/vector_db/faiss.index"

FAISS_METADATA_PATH = "data/vector_db/metadata.json"


# ==================================================
# BGE Embedding 模型
# ==================================================

BGE_MODEL_PATH = "model/bge-small-zh-v1_5"