from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from app.models.document import DocumentCategory, DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    organization_id: str
    claim_id: Optional[str] = None
    category: DocumentCategory
    filename: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    page_count: int
    status: DocumentStatus
    processing_error: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    chunk_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    metadata_json: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    page_count: int
    chunks_created: int
    processing_error: Optional[str] = None

