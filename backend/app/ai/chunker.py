from typing import List, Dict, Any
from app.ai.document_parser import ParsedPage


class ChunkItem:
    def __init__(
        self,
        chunk_index: int,
        page_number: int,
        content: str,
        token_count: int,
        metadata: Dict[str, Any] = None,
    ):
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.token_count = token_count
        self.metadata = metadata or {}


class DocumentChunker:
    """
    Splits document pages into semantic chunks with page provenance,
    overlap, and token estimates.
    """

    def __init__(self, target_chunk_words: int = 250, overlap_words: int = 40):
        self.target_chunk_words = target_chunk_words
        self.overlap_words = overlap_words

    def chunk_pages(self, pages: List[ParsedPage]) -> List[ChunkItem]:
        chunks = []
        global_index = 0

        for page in pages:
            text = page.text.strip()
            if not text:
                continue

            # Split text by paragraphs first
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [text]

            current_chunk_words = []

            for p in paragraphs:
                p_words = p.split()
                if len(current_chunk_words) + len(p_words) <= self.target_chunk_words:
                    current_chunk_words.extend(p_words)
                else:
                    # If current buffer is substantial, flush as a chunk
                    if current_chunk_words:
                        chunk_text = " ".join(current_chunk_words)
                        token_estimate = int(len(current_chunk_words) * 1.3)
                        chunks.append(
                            ChunkItem(
                                chunk_index=global_index,
                                page_number=page.page_number,
                                content=chunk_text,
                                token_count=token_estimate,
                                metadata={"page": page.page_number},
                            )
                        )
                        global_index += 1

                        # Carry over overlap
                        overlap = current_chunk_words[-self.overlap_words :] if len(current_chunk_words) > self.overlap_words else current_chunk_words
                        current_chunk_words = list(overlap) + p_words
                    else:
                        current_chunk_words.extend(p_words)

            # Flush remaining words on this page
            if current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                token_estimate = int(len(current_chunk_words) * 1.3)
                chunks.append(
                    ChunkItem(
                        chunk_index=global_index,
                        page_number=page.page_number,
                        content=chunk_text,
                        token_count=token_estimate,
                        metadata={"page": page.page_number},
                    )
                )
                global_index += 1

        return chunks

