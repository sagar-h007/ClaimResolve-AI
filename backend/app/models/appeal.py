import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class AppealStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class AppealLetter(Base):
    __tablename__ = "appeal_letters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("claim_analyses.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False, default="Formal Medical Necessity Insurance Appeal")
    status = Column(Enum(AppealStatus), default=AppealStatus.DRAFT, nullable=False, index=True)
    current_version = Column(Integer, default=1, nullable=False)

    # Structured Components
    provider_info = Column(JSON, nullable=False, default=dict)
    patient_info = Column(JSON, nullable=False, default=dict)
    claim_info = Column(JSON, nullable=False, default=dict)
    original_denial_details = Column(JSON, nullable=False, default=dict)

    clinical_justification = Column(Text, nullable=False)
    policy_references = Column(Text, nullable=False)
    supporting_evidence = Column(Text, nullable=False)
    request_for_reconsideration = Column(Text, nullable=False)
    supporting_document_references = Column(JSON, nullable=False, default=list)

    # Full compiled letter text for rendering & editing
    full_letter_text = Column(Text, nullable=False)

    # Sign-off & Audit
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    claim = relationship("Claim", back_populates="appeals")
    analysis = relationship("ClaimAnalysis", back_populates="appeal")
    versions = relationship("AppealVersion", back_populates="appeal", cascade="all, delete-orphan", order_by="desc(AppealVersion.version_number)")


class AppealVersion(Base):
    __tablename__ = "appeal_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appeal_id = Column(String(36), ForeignKey("appeal_letters.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    full_letter_text = Column(Text, nullable=False)
    edited_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    appeal = relationship("AppealLetter", back_populates="versions")

