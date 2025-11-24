from pydantic import BaseModel

class TransactionBase(BaseModel):
    type: str  # income / expense
    amount: float
    note: str | None = None
    category_id: str | None = None

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: str

    class Config:
        orm_mode = True
