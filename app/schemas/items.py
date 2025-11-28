from pydantic import BaseModel


class ItemOut(BaseModel):
    id: int
    name: str
    description: str