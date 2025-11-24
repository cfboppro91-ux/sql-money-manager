from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    type = Column(String, nullable=False)  # income / expense
    amount = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
