"""
ingestion/parser.py — Parse PDF files page-by-page using PyMuPDF.

Returns a list of page records:
    {
        "document_name": str,   # original PDF filename (no path)
        "page_number":   int,   # 1-indexed
        "text":          str,   # extracted plain text (cleaned)
    }

Parallel parsing is handled by ProcessPoolExecutor for CPU-bound work.
"""

from __future__ import annotations

import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Iterator

import fitz  # PyMuPDF

from config import PARSE_WORKERS


# ─── single-file parser ───────────────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    """Basic text normalisation: collapse whitespace, remove control chars."""
    # Remove non-printable characters except newlines/tabs
    raw = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", raw)
    # Collapse runs of whitespace (preserve paragraph breaks)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def parse_pdf(pdf_path: str) -> list[dict]:
    """
    Parse a single PDF into a list of page records.
    Skips pages whose extracted text is empty or whitespace-only.
    """
    doc_name = os.path.basename(pdf_path)
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_idx in range(len(doc)):
            text = doc[page_idx].get_text("text")
            text = _clean_text(text)
            if not text:
                continue
            pages.append(
                {
                    "document_name": doc_name,
                    "page_number": page_idx + 1,   # 1-indexed
                    "text": text,
                }
            )
        doc.close()
    except Exception as exc:
        print(f"[parser] WARN: could not parse {pdf_path} — {exc}", file=sys.stderr)
    return pages


# ─── batch parser (parallel) ─────────────────────────────────────────────────

def parse_documents(pdf_paths: list[str], workers: int = PARSE_WORKERS) -> list[dict]:
    """
    Parse multiple PDFs in parallel using a ProcessPoolExecutor.

    Parameters
    ----------
    pdf_paths : absolute paths to PDF files
    workers   : number of parallel processes (default from config)

    Returns
    -------
    Flat list of page records across all documents.
    """
    all_pages: list[dict] = []
    total = len(pdf_paths)
    print(f"[parser] Parsing {total} PDFs with {workers} workers …")

    # For small corpora, skip process overhead
    if total <= workers or workers == 1:
        for p in pdf_paths:
            all_pages.extend(parse_pdf(p))
        print(f"[parser] Extracted {len(all_pages)} pages total.")
        return all_pages

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(parse_pdf, p): p for p in pdf_paths}
        done = 0
        for fut in as_completed(futures):
            try:
                pages = fut.result()
                all_pages.extend(pages)
            except Exception as exc:
                print(f"[parser] WARN: worker error — {exc}", file=sys.stderr)
            done += 1
            if done % 20 == 0 or done == total:
                print(f"[parser] {done}/{total} files parsed …")

    print(f"[parser] Extracted {len(all_pages)} pages total.")
    return all_pages
