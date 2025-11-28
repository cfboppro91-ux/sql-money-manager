from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class FamilyAddRequest(BaseModel):
    email: EmailStr  # email tài khoản muốn link


class FamilyMemberOut(BaseModel):
    id: UUID           # id record family_members
    member_id: UUID    # id của user được xem
    email: str
    total_income: float = 0
    total_expense: float = 0
     total_wallet_balance: float = 0

    class Config:
        orm_mode = True
