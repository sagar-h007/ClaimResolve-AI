import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="organization", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")

