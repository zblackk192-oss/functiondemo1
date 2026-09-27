from pydantic import BaseModel

class RelationModel(BaseModel):
    source: str

    target: str

    type: str