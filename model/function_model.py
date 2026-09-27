from pydantic import BaseModel

class FunctionModel(BaseModel):
    functionId: str
    name: str

    action: str
    object: str
    effect: str

    scenario: str
    constraint: str
    trigger: str

    input: list[str]
    output: list[str]