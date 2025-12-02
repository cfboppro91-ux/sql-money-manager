# app/models/bank_transaction.py
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)

    # 'income' / 'expense' cho đồng bộ với transaction thường
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    # optional: số dư sau giao dịch
    balance_after = Column(Float, nullable=True)

    account = relationship("BankAccount", back_populates="transactions")
