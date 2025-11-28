# schema/transaction.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
class TransactionBase(BaseModel):
    type: str  # income / expense
    amount: float
    note: str | None = None
    category_id: UUID | None = None  # 🔥 sửa lại
    date: datetime | None = None

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: UUID  # 🔥 sửa lại

    class Config:
        orm_mode = True
