from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentCategory
from app.ai.embedding_provider import get_embedding_provider
from app.ai.vector_store import VectorStore, VectorSearchResult


class PayerPolicyRetriever:
    """
    Step 3: Payer Policy Retrieval.
    Retrieves the governing sections from the payer's policy guidelines,
    covering medical necessity criteria, coverage prerequisites, and appeal deadlines.
    """

    @classmethod
    async def retrieve_policy_sections(
        cls,
        db: AsyncSession,
        claim_id: str,
        procedure_codes: List[str],
        denial_code: str,
        denial_reason: str,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        embedder = get_embedding_provider()

        query_text = f"Payer medical coverage policy requirements {' '.join(procedure_codes)} {denial_code} {denial_reason}"
        query_vector = await embedder.get_embedding(query_text)

        results = await VectorStore.search(
            db=db,
            query_vector=query_vector,
            claim_id=claim_id,
            category=DocumentCategory.PAYER_POLICY,
            top_k=top_k,
        )

        return results

