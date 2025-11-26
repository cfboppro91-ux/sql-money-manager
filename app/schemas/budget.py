# schema/budget.py
from pydantic import BaseModel
from uuid import UUID  # 👈 thêm cái này

class BudgetBase(BaseModel):
    amount: float
    period: str  # day / month / year
    type: str    # overall / category
    category_id: UUID | None = None  # 👈 đổi từ str sang UUID
    is_active: bool = True

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: UUID  # 👈 đổi từ str sang UUID

    class Config:
        orm_mode = True
        # from_attributes = True  # nếu là Pydantic v2
