from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    period = Column(String, default="month")
    type = Column(String, default="overall")
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    is_active = Column(String, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
