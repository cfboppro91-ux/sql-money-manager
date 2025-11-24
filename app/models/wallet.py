from sqlalchemy import Column, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    balance = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
