"""
api/download_docs.py — Async download of up to 200 encrypted PDF documents.

Decrypts each PDF (if a password is supplied) using PyMuPDF after download.
Falls back to plain binary write when no password is needed.
"""

import asyncio
import os
import sys
import aiohttp
import fitz                        # PyMuPDF
from config import (
    API_BASE_URL,
    DOCS_DIR,
    DOWNLOAD_CONCURRENCY,
    NUM_DOCS,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _decrypt_and_save(encrypted_bytes: bytes, dest_path: str, password: str) -> None:
    """Open encrypted PDF from memory, decrypt, save as plain PDF."""
    doc = fitz.open(stream=encrypted_bytes, filetype="pdf")
    if doc.is_encrypted:
        if not doc.authenticate(password):
            raise ValueError(f"Wrong password for {os.path.basename(dest_path)}")
    doc.save(dest_path, garbage=4, deflate=True)
    doc.close()


async def _download_one(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    dest_path: str,
    password: str | None,
) -> None:
    """Download a single document and optionally decrypt it."""
    async with sem:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                raw = await resp.read()

            if password:
                _decrypt_and_save(raw, dest_path, password)
            else:
                with open(dest_path, "wb") as f:
                    f.write(raw)
        except Exception as exc:
            print(f"[download] WARN: failed {url} — {exc}", file=sys.stderr)


# ─── public API ───────────────────────────────────────────────────────────────

async def download_documents_async(
    doc_list: list[dict],
    password: str | None = None,
    token: str | None = None,
) -> list[str]:
    """
    Download all documents concurrently.

    Parameters
    ----------
    doc_list : list of dicts with at least {"url": str, "name": str}
    password : decryption password returned by /register
    token    : bearer token for authenticated endpoints

    Returns
    -------
    List of local file paths that were successfully saved.
    """
    os.makedirs(DOCS_DIR, exist_ok=True)
    sem = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    tasks = []
    dest_paths = []

    connector = aiohttp.TCPConnector(limit=DOWNLOAD_CONCURRENCY)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        for doc in doc_list:
            fname = doc.get("name") or os.path.basename(doc["url"])
            if not fname.endswith(".pdf"):
                fname += ".pdf"
            dest = os.path.join(DOCS_DIR, fname)
            dest_paths.append(dest)
            tasks.append(
                _download_one(session, sem, doc["url"], dest, password)
            )

        print(f"[download] Downloading {len(tasks)} documents …")
        await asyncio.gather(*tasks)

    # return only files that actually exist
    saved = [p for p in dest_paths if os.path.exists(p)]
    print(f"[download] {len(saved)}/{len(tasks)} documents saved to {DOCS_DIR}")
    return saved


def fetch_doc_list(token: str) -> list[dict]:
    """
    GET /documents  →  list of {"url": ..., "name": ...} dicts.
    Synchronous wrapper (called once before the async download loop).
    """
    import requests
    url = f"{API_BASE_URL}/documents"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Normalise: API may return {"documents": [...]} or directly [...]
    if isinstance(data, list):
        return data
    return data.get("documents", data.get("docs", []))


def download_documents(
    doc_list: list[dict],
    password: str | None = None,
    token: str | None = None,
) -> list[str]:
    """Synchronous entry-point that runs the async downloader."""
    return asyncio.run(download_documents_async(doc_list, password, token))
