# app/schemas/user.py
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID            # trước là str
    email: EmailStr

    # thay cho orm_mode = True trong Pydantic v1
    model_config = ConfigDict(from_attributes=True)