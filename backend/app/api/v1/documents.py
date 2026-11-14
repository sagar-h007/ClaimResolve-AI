from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentCategory, DocumentStatus
from app.models.claim import Claim
from app.schemas.document import DocumentResponse, DocumentChunkResponse, DocumentStatusResponse
from app.services.document_service import DocumentService
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Form(...),
    claim_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If claim_id is provided, verify it belongs to user's org
    if claim_id:
        c_res = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
        )
        if not c_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found in organization")

    doc = await DocumentService.process_uploaded_file(
        db=db,
        file=file,
        organization_id=current_user.organization_id,
        category=category,
        claim_id=claim_id,
    )

    # Count chunks
    chunk_res = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunks = chunk_res.scalars().all()

    return DocumentResponse(
        id=doc.id,
        organization_id=doc.organization_id,
        claim_id=doc.claim_id,
        category=doc.category,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        page_count=doc.page_count,
        status=doc.status,
        processing_error=doc.processing_error,
        metadata_json=doc.metadata_json or {},
        chunk_count=len(chunks),
        created_at=doc.created_at,
    )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    claim_id: Optional[str] = Query(None),
    category: Optional[DocumentCategory] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Document)
        .where(Document.organization_id == current_user.organization_id)
        .options(selectinload(Document.chunks))
        .order_by(desc(Document.created_at))
    )

    if claim_id:
        query = query.where(Document.claim_id == claim_id)
    if category:
        query = query.where(Document.category == category)

    res = await db.execute(query)
    docs = res.scalars().all()

    items = []
    for d in docs:
        items.append(
            DocumentResponse(
                id=d.id,
                organization_id=d.organization_id,
                claim_id=d.claim_id,
                category=d.category,
                filename=d.filename,
                original_filename=d.original_filename,
                file_size_bytes=d.file_size_bytes,
                mime_type=d.mime_type,
                page_count=d.page_count,
                status=d.status,
                processing_error=d.processing_error,
                metadata_json=d.metadata_json or {},
                chunk_count=len(d.chunks) if d.chunks else 0,
                created_at=d.created_at,
            )
        )
    return items


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id, Document.organization_id == current_user.organization_id)
        .options(selectinload(Document.chunks))
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentResponse(
        id=doc.id,
        organization_id=doc.organization_id,
        claim_id=doc.claim_id,
        category=doc.category,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        page_count=doc.page_count,
        status=doc.status,
        processing_error=doc.processing_error,
        metadata_json=doc.metadata_json or {},
        chunk_count=len(doc.chunks) if doc.chunks else 0,
        created_at=doc.created_at,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id, Document.organization_id == current_user.organization_id)
        .options(selectinload(Document.chunks))
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentStatusResponse(
        document_id=doc.id,
        status=doc.status,
        page_count=doc.page_count,
        chunks_created=len(doc.chunks) if doc.chunks else 0,
        processing_error=doc.processing_error,
    )


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify doc exists and belongs to user's org
    doc_res = await db.execute(
        select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id)
    )
    if not doc_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    return chunks


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    return None

