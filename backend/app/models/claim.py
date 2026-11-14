import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ClaimStatus(str, enum.Enum):
    UPLOADED = "Uploaded"
    PROCESSING = "Processing"
    ANALYSIS_COMPLETE = "Analysis Complete"
    APPEAL_DRAFTED = "Appeal Drafted"
    PENDING_REVIEW = "Pending Review"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    claim_number = Column(String(100), nullable=False, unique=True, index=True)
    payer_name = Column(String(255), nullable=False, index=True)
    policy_number_masked = Column(String(100), nullable=False)
    procedure_codes = Column(JSON, nullable=False, default=list)  # e.g. ["99214", "73721"]
    diagnosis_codes = Column(JSON, nullable=False, default=list)  # e.g. ["M25.561"]
    claim_amount = Column(Float, nullable=False, default=0.0)
    denied_amount = Column(Float, nullable=False, default=0.0)
    denial_date = Column(String(30), nullable=True)
    denial_reason = Column(Text, nullable=True)
    denial_code = Column(String(50), nullable=True, index=True)
    claim_status = Column(Enum(ClaimStatus), default=ClaimStatus.UPLOADED, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="claims")
    patient = relationship("Patient", back_populates="claims")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")
    analyses = relationship("ClaimAnalysis", back_populates="claim", cascade="all, delete-orphan")
    appeals = relationship("AppealLetter", back_populates="claim", cascade="all, delete-orphan")

