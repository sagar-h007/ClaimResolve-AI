from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentCategory
from app.ai.embedding_provider import get_embedding_provider
from app.ai.vector_store import VectorStore, VectorSearchResult


class ClinicalEvidenceRetriever:
    """
    Step 2: Clinical Evidence Retrieval.
    Searches patient medical records using semantic vector retrieval for
    physician notes, conservative therapies, lab/imaging results, and necessity statements.
    """

    @classmethod
    async def retrieve_clinical_evidence(
        cls,
        db: AsyncSession,
        claim_id: str,
        denial_reason: str,
        required_items: List[str],
        top_k: int = 6,
    ) -> List[VectorSearchResult]:
        embedder = get_embedding_provider()

        # Build focused query combining denial context with required documentation
        query_text = f"Clinical justification: {denial_reason} {' '.join(required_items)}"
        query_vector = await embedder.get_embedding(query_text)

        results = await VectorStore.search(
            db=db,
            query_vector=query_vector,
            claim_id=claim_id,
            category=DocumentCategory.CLINICAL_RECORD,
            top_k=top_k,
        )

        return results

