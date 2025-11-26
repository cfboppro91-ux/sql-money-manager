# schemas/budget.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class BudgetBase(BaseModel):
    amount: float
    period: str  # day / month / year
    type: str    # overall / category
    category_id: UUID | None = None
    is_active: bool = True


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Optional[float] = None
    period: Optional[str] = None        # day / month / year
    type: Optional[str] = None          # overall / category
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class BudgetOut(BudgetBase):
    id: UUID

    class Config:
        orm_mode = True
        # from_attributes = True  # nếu dùng Pydantic v2
