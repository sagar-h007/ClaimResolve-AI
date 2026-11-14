import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    external_patient_id = Column(String(100), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(String(20), nullable=False)
    gender = Column(String(20), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    payer_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="patients")
    claims = relationship("Claim", back_populates="patient", cascade="all, delete-orphan")

