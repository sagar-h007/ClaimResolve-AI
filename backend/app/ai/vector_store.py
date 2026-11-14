import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.document import Document, DocumentChunk, DocumentCategory
from app.models.vector_type import HAS_PGVECTOR
from app.database import is_sqlite


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorSearchResult:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        document_category: str,
        document_filename: str,
        page_number: int,
        content: str,
        score: float,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_category = document_category
        self.document_filename = document_filename
        self.page_number = page_number
        self.content = content
        self.score = round(score, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_category": self.document_category,
            "document_filename": self.document_filename,
            "page_number": self.page_number,
            "content": self.content,
            "score": self.score,
        }


class VectorStore:
    """
    RAG Vector Store supporting PostgreSQL with pgvector as well as
    in-database / SQLite cosine retrieval.
    """

    @staticmethod
    async def search(
        db: AsyncSession,
        query_vector: List[float],
        claim_id: Optional[str] = None,
        category: Optional[DocumentCategory] = None,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        # Query chunks with their parent document
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(selectinload(DocumentChunk.document))
        )

        if claim_id:
            stmt = stmt.where(Document.claim_id == claim_id)
        if category:
            stmt = stmt.where(Document.category == category)

        # If PostgreSQL with pgvector is active, we can leverage pgvector operators
        if not is_sqlite and HAS_PGVECTOR:
            try:
                # pgvector cosine distance: DocumentChunk.embedding.cosine_distance(query_vector)
                distance_stmt = stmt.order_by(
                    DocumentChunk.embedding.cosine_distance(query_vector)
                ).limit(top_k)
                result = await db.execute(distance_stmt)
                chunks = result.scalars().all()
                results = []
                for c in chunks:
                    # Score approximation from cosine distance
                    sim = 1.0 - (c.embedding.cosine_distance(query_vector) if hasattr(c.embedding, 'cosine_distance') else 0.1)
                    results.append(
                        VectorSearchResult(
                            chunk_id=c.id,
                            document_id=c.document_id,
                            document_category=c.document.category.value if c.document else "unknown",
                            document_filename=c.document.original_filename if c.document else "document",
                            page_number=c.page_number,
                            content=c.content,
                            score=max(0.5, min(1.0, float(sim))),
                        )
                    )
                return results
            except Exception:
                # Fallback to python calculation below if vector operator fails
                pass

        # Standard / SQLite evaluation
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        scored_chunks = []
        for c in chunks:
            if not c.embedding:
                continue
            emb = c.embedding
            if isinstance(emb, list):
                score = cosine_similarity(query_vector, emb)
                scored_chunks.append((score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:top_k]

        output = []
        for score, c in top_chunks:
            output.append(
                VectorSearchResult(
                    chunk_id=c.id,
                    document_id=c.document_id,
                    document_category=c.document.category.value if c.document else "unknown",
                    document_filename=c.document.original_filename if c.document else "document",
                    page_number=c.page_number,
                    content=c.content,
                    score=score,
                )
            )

        return output

