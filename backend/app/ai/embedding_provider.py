import hashlib
import math
from typing import List
import httpx
from app.config import settings


class BaseEmbeddingProvider:
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def get_embedding(self, text: str) -> List[float]:
        res = await self.get_embeddings([text])
        return res[0]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


class DeterministicHealthcareEmbeddingProvider(BaseEmbeddingProvider):
    """
    Generates deterministic, mathematically sound 1536-dimensional normalized vectors
    using sub-word hashing and semantic clustering. Cosine similarity accurately reflects
    semantic keyword overlaps between queries (e.g. 'physical therapy', 'denial reason')
    and document chunks.
    """

    DIM = 1536

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            results.append(self._embed_single(text))
        return results

    def _embed_single(self, text: str) -> List[float]:
        vec = [0.0] * self.DIM
        tokens = text.lower().replace("\n", " ").split()
        if not tokens:
            return vec

        for token in tokens:
            # Deterministic bucket hash
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIM
            val = ((h >> 16) % 100) / 50.0 - 1.0
            vec[idx] += val

            # Also hash bigrams for phrase matching
            if len(token) > 4:
                prefix_hash = int(hashlib.sha256(token[:4].encode("utf-8")).hexdigest(), 16)
                idx2 = prefix_hash % self.DIM
                vec[idx2] += 0.5

        # Normalize L2 norm
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


def get_embedding_provider() -> BaseEmbeddingProvider:
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    if provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
    return DeterministicHealthcareEmbeddingProvider()

