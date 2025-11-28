from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

class FamilyLink(Base):
    """
    Quan hệ: owner (người đang đăng nhập) có thể xem dữ liệu của member
    """
    __tablename__ = "family_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_id", "member_id", name="uq_family_owner_member"),
    )
