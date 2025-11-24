from pydantic import BaseModel

class BudgetBase(BaseModel):
    amount: float
    period: str  # day / month / year
    type: str    # overall / category
    category_id: str | None = None
    is_active: bool = True

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: str
    class Config:
        orm_mode = True
