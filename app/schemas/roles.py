from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str


class RoleOut(BaseModel):
    id: int

    model_config = {
        "from_attributes": True
    }


class ChangeUserRole(BaseModel):
    user_id: int
    role_id: int