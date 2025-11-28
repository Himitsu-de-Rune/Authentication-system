from pydantic import BaseModel


class PermissionBase(BaseModel):
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    role_id: int


class PermissionOut(PermissionBase):
    id: int
    role_id: int

    model_config = {
        "from_attributes": True
    }