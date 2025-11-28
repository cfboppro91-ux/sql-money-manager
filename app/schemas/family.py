from pydantic import BaseModel, EmailStr
from uuid import UUID

class FamilyMemberBase(BaseModel):
    member_id: UUID
    email: EmailStr

class FamilyMemberOut(FamilyMemberBase):
    total_income: float = 0
    total_expense: float = 0

    class Config:
        orm_mode = True

class FamilyAddRequest(BaseModel):
    email: EmailStr
