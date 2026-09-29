from pydantic import BaseModel, Field


class FunctionModel(BaseModel):
    id: str
    name: str = ""

    actor: str = ""
    action: str = ""
    object: str = ""
    effect: str = ""
    trigger: str = ""
    condition: str = ""

    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)

    # 当前架构中的扩展字段继续保留。
    scenario: str = ""
    constraint: str = ""
