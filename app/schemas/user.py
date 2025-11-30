# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr

    class Config:
        orm_mode = True


class FCMTokenIn(BaseModel):
    fcm_token: str
