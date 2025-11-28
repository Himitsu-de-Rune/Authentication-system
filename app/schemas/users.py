from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserOut(UserBase):
    id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    role: Optional[str]

    model_config = {
        "from_attributes": True
    }