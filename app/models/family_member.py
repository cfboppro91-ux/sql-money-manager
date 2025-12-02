# app/models/family_member.py
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    group_name = Column(String, nullable=True)

    # trạng thái: pending / accepted / rejected
    status = Column(String, nullable=False, server_default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

