import json
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    status
)


# ============================================================
# 加载环境变量
# ============================================================

load_dotenv()


# ============================================================
# 配置
# ============================================================

RESULT_API_TOKEN = os.getenv(
    "RESULT_API_TOKEN",
    ""
).strip()

RESULT_STORE_PATH = Path(
    os.getenv(
        "RESULT_STORE_PATH",
        "output/published_result.json"
    )
)

result_file_lock = threading.Lock()


# ============================================================
# FastAPI应用
# ============================================================

app = FastAPI(
    title="功能补全结果API",
    description="接收功能补全服务的输出，并向下游提供最新结果",
    version="1.0.0"
)


# ============================================================
# Token认证
# ============================================================

def verify_api_token(
    authorization: Optional[str] = Header(
        default=None
    )
):

    if not RESULT_API_TOKEN:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="结果API尚未配置RESULT_API_TOKEN"
        )

    expected_token = (
        f"Bearer {RESULT_API_TOKEN}"
    )

    supplied_token = (
        authorization
        or ""
    )

    if not secrets.compare_digest(
        supplied_token,
        expected_token
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


# ============================================================
# 校验补全结果
# ============================================================

def validate_result(
    result: Dict[str, Any]
):

    required_fields = [
        "retrieval",
        "llm_result",
        "completion_result"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing_fields:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "补全结果缺少必要字段",
                "missing_fields": missing_fields
            }
        )

    completion_result = result.get(
        "completion_result"
    )

    if not isinstance(
        completion_result,
        dict
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "completion_result必须是JSON对象"
            )
        )

    functions = completion_result.get(
        "functions"
    )

    relations = completion_result.get(
        "relations"
    )

    if not isinstance(
        functions,
        list
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "completion_result.functions必须是数组"
            )
        )

    if not isinstance(
        relations,
        list
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "completion_result.relations必须是数组"
            )
        )


# ============================================================
# 原子保存结果
# ============================================================

def save_result_record(
    record: Dict[str, Any]
):

    RESULT_STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = (
        RESULT_STORE_PATH.parent
        / (
            f".{RESULT_STORE_PATH.name}."
            f"{uuid4().hex}.tmp"
        )
    )

    try:

        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                record,
                file,
                ensure_ascii=False,
                indent=2
            )

            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(
            temporary_path,
            RESULT_STORE_PATH
        )

    finally:

        if temporary_path.exists():

            temporary_path.unlink()


# ============================================================
# 读取最新结果
# ============================================================

def load_latest_result():

    if not RESULT_STORE_PATH.exists():

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目前还没有已发布的补全结果"
        )

    try:

        with RESULT_STORE_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except json.JSONDecodeError as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器保存的结果文件不是有效JSON"
        ) from e


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "token_configured": bool(
            RESULT_API_TOKEN
        ),
        "result_available": (
            RESULT_STORE_PATH.exists()
        ),
        "store_path": str(
            RESULT_STORE_PATH
        )
    }


# ============================================================
# 接收并发布结果
# ============================================================

@app.post(
    "/api/v1/results",
    status_code=status.HTTP_201_CREATED
)
def receive_result(
    result: Dict[str, Any],
    _: None = Depends(
        verify_api_token
    )
):

    validate_result(
        result
    )

    result_id = uuid4().hex

    published_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    record = {
        "success": True,
        "result_id": result_id,
        "published_at": published_at,
        "result": result
    }

    with result_file_lock:

        save_result_record(
            record
        )

    return {
        "success": True,
        "message": "补全结果发布成功",
        "result_id": result_id,
        "published_at": published_at
    }


# ============================================================
# 下游获取最新结果
# ============================================================

@app.get("/api/v1/results/latest")
def get_latest_result(
    _: None = Depends(
        verify_api_token
    )
):

    with result_file_lock:

        return load_latest_result()