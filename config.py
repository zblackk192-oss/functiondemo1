import os


HISTORY_CASE_DIR = "data/history_cases"


CURRENT_CASE_PATH = (
    "data/current_case.json"
)


OUTPUT_PATH = (
    "output/result.json"
)


SEMANTIC_GRAPH_PATH = (
    "output/semantic_graph.json"
)
# Qwen配置

QWEN_API_KEY = (
    "sk-ws-H.PMMLYEX.iTON.MEYCIQDUIkKBrxmHDkwGhkWLvbXqmEE3WT95ml1BPvVKquu7tgIhANpUiW_TW9cN5q4uowEE2EyHmyk2Lzw_PwC_pdx0mbEL"
)


QWEN_BASE_URL = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)


QWEN_MODEL = (
    "qwen3.8-max"
)

# ==================================================
# RAG向量知识库
# ==================================================

VECTOR_DB_DIR = (
    "data/vector_db"
)

FAISS_INDEX_PATH = (
    "data/vector_db/faiss.index"
)

FAISS_METADATA_PATH = (
    "data/vector_db/metadata.json"
)

# BGE Embedding模型
BGE_MODEL_PATH = (
    "model/bge-small-zh-v1_5"
)