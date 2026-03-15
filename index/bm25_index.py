"""
index/bm25_index.py — Build and query a BM25 index over parsed page records.

Each "document" in the BM25 index is one PDF page.
"""

from __future__ import annotations

import re
import string
from typing import NamedTuple

import numpy as np
from rank_bm25 import BM25Okapi

from config import BM25_TOP_K


# ─── simple tokeniser ─────────────────────────────────────────────────────────

_PUNCT = str.maketrans("", "", string.punctuation)

def tokenise(text: str) -> list[str]:
    """Lowercase, remove punctuation, split on whitespace."""
    text = text.lower().translate(_PUNCT)
    return text.split()


# ─── index ────────────────────────────────────────────────────────────────────

class BM25Index:
    """Wrapper around BM25Okapi that preserves page metadata."""

    def __init__(self, pages: list[dict]):
        """
        Parameters
        ----------
        pages : list of {"document_name", "page_number", "text"} dicts
        """
        if not pages:
            raise ValueError("Cannot build BM25 index from empty page list.")

        self._pages = pages
        tokenised = [tokenise(p["text"]) for p in pages]
        self._bm25 = BM25Okapi(tokenised)
        print(f"[bm25] Index built over {len(pages)} pages.")

    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[dict]:
        """
        Search the index and return the top-k page records.

        Returns
        -------
        list of page dicts, each enriched with a "score" key, sorted
        descending by BM25 score.
        """
        tokens = tokenise(query)
        if not tokens:
            return []

        scores: np.ndarray = self._bm25.get_scores(tokens)
        # argsort descending
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                record = dict(self._pages[idx])  # copy
                record["score"] = float(scores[idx])
                results.append(record)

        return results

    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._pages)


def build_index(pages: list[dict]) -> BM25Index:
    """Convenience function: build and return a BM25Index from page records."""
    return BM25Index(pages)
