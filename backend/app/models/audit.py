import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

