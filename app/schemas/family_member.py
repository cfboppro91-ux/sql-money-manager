# app/schemas/family_member.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class FamilyAddRequest(BaseModel):
    email: EmailStr
    display_name: str | None = None


class FamilyMemberOut(BaseModel):
    id: UUID
    member_id: UUID
    email: str
    display_name: str | None = None
    total_income: float = 0
    total_expense: float = 0
    total_wallet_balance: float = 0
    status: str = "accepted"   # ✅ thêm

    class Config:
        orm_mode = True


# ✅ schema riêng cho lời mời (bên người ĐƯỢC mời nhìn thấy)
class FamilyInvitationOut(BaseModel):
    id: UUID              # id record family_members
    owner_id: UUID        # user đã mời mình
    owner_email: str
    owner_display_name: str | None = None
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
