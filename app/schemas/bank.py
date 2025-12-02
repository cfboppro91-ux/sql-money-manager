# app/schemas/bank.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class BankTransactionOut(BaseModel):
    id: UUID
    type: str
    amount: float
    description: str | None = None
    date: datetime

    class Config:
        from_attributes = True  # pydantic v2


class BankAccountOut(BaseModel):
    id: UUID
    bank_name: str
    account_number: str
    balance: float

    class Config:
        from_attributes = True


class SimulateTxIn(BaseModel):
    type: str   # "income" / "expense"
    amount: float
    description: str | None = None