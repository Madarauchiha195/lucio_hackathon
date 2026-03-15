"""
qa/retriever.py — BM25-based retrieval layer for question answering.

Wraps BM25Index.search and formats context for the LLM.
"""

from __future__ import annotations

from index.bm25_index import BM25Index
from config import BM25_TOP_K


def retrieve(query: str, index: BM25Index, top_k: int = BM25_TOP_K) -> list[dict]:
    """
    Return up to top_k page records most relevant to the query.

    Each record: {"document_name", "page_number", "text", "score"}
    """
    return index.search(query, top_k=top_k)


def build_context(pages: list[dict]) -> str:
    """
    Concatenate retrieved page texts into a numbered context string
    suitable for the Gemini prompt.
    """
    parts = []
    for i, page in enumerate(pages, 1):
        header = (
            f"[Context {i}] "
            f"Document: {page['document_name']} | "
            f"Page: {page['page_number']}"
        )
        parts.append(f"{header}\n{page['text']}")
    return "\n\n---\n\n".join(parts)
