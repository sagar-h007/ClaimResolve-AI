import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models.document import Document, DocumentChunk, DocumentCategory, DocumentStatus
from app.ai.document_parser import DocumentParser
from app.ai.chunker import DocumentChunker
from app.ai.embedding_provider import get_embedding_provider

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


class DocumentService:
    @staticmethod
    async def process_uploaded_file(
        db: AsyncSession,
        file: UploadFile,
        organization_id: str,
        category: DocumentCategory,
        claim_id: Optional[str] = None,
    ) -> Document:
        filename = file.filename or "unknown_file.pdf"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Secure storage directory
        org_dir = os.path.join(settings.UPLOAD_DIR, organization_id, claim_id or "general")
        os.makedirs(org_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        dest_path = os.path.join(org_dir, unique_filename)

        content = await file.read()
        file_size = len(content)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
            )

        with open(dest_path, "wb") as f:
            f.write(content)

        # Create Document record
        doc_record = Document(
            organization_id=organization_id,
            claim_id=claim_id,
            category=category,
            filename=unique_filename,
            original_filename=filename,
            file_path=dest_path,
            file_size_bytes=file_size,
            mime_type=file.content_type or "application/octet-stream",
            page_count=1,
            status=DocumentStatus.PROCESSING,
        )
        db.add(doc_record)
        await db.flush()

        try:
            # Parse pages
            pages = DocumentParser.parse_document(dest_path, filename)
            doc_record.page_count = max(1, len(pages))

            # Chunk document
            chunker = DocumentChunker(target_chunk_words=250, overlap_words=40)
            chunk_items = chunker.chunk_pages(pages)

            if chunk_items:
                # Embed chunks
                embedder = get_embedding_provider()
                chunk_texts = [ci.content for ci in chunk_items]
                embeddings = await embedder.get_embeddings(chunk_texts)

                for idx, ci in enumerate(chunk_items):
                    chunk_obj = DocumentChunk(
                        document_id=doc_record.id,
                        chunk_index=ci.chunk_index,
                        page_number=ci.page_number,
                        content=ci.content,
                        token_count=ci.token_count,
                        embedding=embeddings[idx] if idx < len(embeddings) else None,
                        metadata_json=ci.metadata,
                    )
                    db.add(chunk_obj)

            doc_record.status = DocumentStatus.PROCESSED
            doc_record.metadata_json = {
                "chunks_count": len(chunk_items),
                "extracted_pages": len(pages),
            }
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}", exc_info=True)
            doc_record.status = DocumentStatus.FAILED
            doc_record.processing_error = str(e)

        await db.commit()
        await db.refresh(doc_record)
        return doc_record

