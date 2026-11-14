import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceStrength(str, enum.Enum):
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"
    INSUFFICIENT = "Insufficient"


class ClaimAnalysis(Base):
    __tablename__ = "claim_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False, index=True)
    denial_reason = Column(Text, nullable=True)
    denial_code = Column(String(50), nullable=True)
    payer_explanation = Column(Text, nullable=True)
    policy_section = Column(String(255), nullable=True)
    policy_requirements_summary = Column(Text, nullable=True)
    clinical_findings_summary = Column(Text, nullable=True)

    evidence_strength = Column(Enum(EvidenceStrength), default=EvidenceStrength.MODERATE, nullable=False)
    missing_evidence = Column(JSON, nullable=False, default=list)  # list of strings
    conflicting_information = Column(JSON, nullable=False, default=list)  # list of strings
    potential_appeal_arguments = Column(JSON, nullable=False, default=list)  # list of strings
    recommended_next_steps = Column(JSON, nullable=False, default=list)  # list of strings
    risk_indicators = Column(JSON, nullable=False, default=list)  # list of strings/objects
    raw_llm_output = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    claim = relationship("Claim", back_populates="analyses")
    evidence_references = relationship("EvidenceReference", back_populates="analysis", cascade="all, delete-orphan")
    appeal = relationship("AppealLetter", back_populates="analysis", uselist=False)


class EvidenceReference(Base):
    __tablename__ = "evidence_references"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("claim_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)

    document_type = Column(String(50), nullable=False)  # "clinical_record", "payer_policy", "denial_letter"
    source_document_title = Column(String(255), nullable=False)
    page_number = Column(String(50), nullable=False, default="1")
    citation_text = Column(Text, nullable=False)
    extracted_text = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=False, default=0.85)
    is_supporting = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    analysis = relationship("ClaimAnalysis", back_populates="evidence_references")
    chunk = relationship("DocumentChunk", back_populates="evidence_references")

