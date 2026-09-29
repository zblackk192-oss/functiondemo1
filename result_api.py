import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
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

RESULT_STORE_PATH = Path(
    os.getenv(
        "RESULT_STORE_PATH",
        "output/published_result.json"
    )
)

result_file_lock = threading.Lock()

RESULT_SCHEMA_VERSION = (
    "input-compatible-v2"
)


# ============================================================
# FastAPI应用
# ============================================================

app = FastAPI(
    title="功能补全结果API",
    description="接收功能补全服务的输出，并向下游提供最新结果",
    version="2.0.0"
)


# ============================================================
# 校验补全结果
# ============================================================

def validate_result(
    result: Dict[str, Any]
):

    required_fields = [
        "request_id",
        "status",
        "result",
        "error"
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
                "message": "发布结果缺少必要字段",
                "missing_fields": missing_fields
            }
        )

    payload_result = result.get(
        "result"
    )

    if not isinstance(
        payload_result,
        dict
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="result必须是JSON对象"
        )

    function_point_set = payload_result.get(
        "function_point_set"
    )

    if not isinstance(
        function_point_set,
        dict
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="result.function_point_set必须是JSON对象"
        )

    function_set_required_fields = [
        "raw_text",
        "function_points",
        "summary"
    ]

    missing_function_set_fields = [
        field
        for field in function_set_required_fields
        if field not in function_point_set
    ]

    if missing_function_set_fields:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "function_point_set缺少必要字段",
                "missing_fields": missing_function_set_fields
            }
        )

    function_points = function_point_set.get(
        "function_points"
    )

    relations = payload_result.get(
        "relations"
    )

    if not isinstance(function_points, list):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "result.function_point_set."
                "function_points必须是数组"
            )
        )

    if not isinstance(relations, list):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="result.relations必须是数组"
        )

    event_required_fields = {
        "actor",
        "action",
        "object",
        "effect",
        "trigger",
        "condition",
        "inputs",
        "outputs",
        "preconditions",
        "postconditions"
    }

    for index, function_point in enumerate(function_points):

        if not isinstance(function_point, dict):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "function_points"
                    f"[{index}]必须是JSON对象"
                )
            )

        if not function_point.get("id"):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "function_points"
                    f"[{index}].id不能为空"
                )
            )

        event = function_point.get("event")

        if not isinstance(event, dict):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "function_points"
                    f"[{index}].event必须是JSON对象"
                )
            )

        missing_event_fields = sorted(
            event_required_fields.difference(event)
        )

        if missing_event_fields:

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail={
                    "message": (
                        "event缺少必要字段"
                    ),
                    "index": index,
                    "missing_fields": missing_event_fields
                }
            )

    relation_required_fields = {
        "source",
        "target",
        "source_name",
        "target_name",
        "relation_type",
        "direction",
        "confidence",
        "evidence"
    }

    for index, relation in enumerate(relations):

        if not isinstance(relation, dict):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"relations[{index}]必须是JSON对象"
                )
            )

        missing_relation_fields = sorted(
            relation_required_fields.difference(relation)
        )

        if missing_relation_fields:

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail={
                    "message": (
                        "relation缺少必要字段"
                    ),
                    "index": index,
                    "missing_fields": missing_relation_fields
                }
            )

        if not relation.get("source"):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"relations[{index}].source不能为空"
                )
            )

        if not relation.get("target"):

            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"relations[{index}].target不能为空"
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

    except OSError as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "读取服务器结果文件失败："
                f"{e}"
            )
        ) from e


# ============================================================
# 根路径
# ============================================================

@app.get("/")
def root():

    return {
        "service": "功能补全结果API",
        "status": "running",
        "schema_version": RESULT_SCHEMA_VERSION,
        "health_url": "/health",
        "publish_url": "/api/v1/results",
        "latest_result_url": "/api/v1/results/latest"
    }


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "schema_version": RESULT_SCHEMA_VERSION,
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
    result: Dict[str, Any]
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

    try:

        with result_file_lock:

            save_result_record(
                result
            )

    except OSError as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "保存补全结果失败："
                f"{e}"
            )
        ) from e

    return {
        "success": True,
        "message": "补全结果发布成功",
        "schema_version": RESULT_SCHEMA_VERSION,
        "result_id": result_id,
        "published_at": published_at
    }


# ============================================================
# 下游获取最新结果
# ============================================================

@app.get("/api/v1/results/latest")
def get_latest_result():

    with result_file_lock:

        return load_latest_result()
