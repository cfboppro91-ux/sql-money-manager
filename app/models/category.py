from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
