# app/schemas/bank.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


# --------- BANK ACCOUNT ---------
class BankAccountBase(BaseModel):
    bank_name: str
    account_number: str
    balance: float = 0.0


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountOut(BankAccountBase):
    id: UUID

    class Config:
        orm_mode = True


# --------- BANK TRANSACTION ---------
class BankTransactionBase(BaseModel):
    type: str           # 'income' hoặc 'expense'
    amount: float
    description: Optional[str] = None
    date: Optional[datetime] = None


class BankTransactionCreate(BankTransactionBase):
    pass


class BankTransactionOut(BankTransactionBase):
    id: UUID
    account_id: UUID
    balance_after: Optional[float] = None

    class Config:
        orm_mode = True
