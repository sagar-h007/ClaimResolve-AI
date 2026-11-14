import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.vector_type import VectorType


class DocumentCategory(str, enum.Enum):
    DENIAL_LETTER = "denial_letter"
    CLINICAL_RECORD = "clinical_record"
    PAYER_POLICY = "payer_policy"
    BILLING_DOCUMENT = "billing_document"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=True, index=True)

    category = Column(Enum(DocumentCategory), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    processing_error = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="documents")
    claim = relationship("Claim", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    embedding = Column(VectorType(1536), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    evidence_references = relationship("EvidenceReference", back_populates="chunk", cascade="all, delete-orphan")

