from typing import Any

from pydantic import BaseModel


class RelationModel(BaseModel):
    source: str
    target: str
    source_name: str = ""
    target_name: str = ""
    relation_type: str = "dependency"
    direction: str = "source_to_target"
    confidence: float = 0.0
    evidence: Any = ""

    # 当前架构中的扩展字段继续保留。
    flowObject: str = ""