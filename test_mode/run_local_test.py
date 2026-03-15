"""
test_mode/run_local_test.py — Local test mode.

Loads up to 20 PDF files from the sample_docs folder (or any local folder),
parses them, builds a BM25 index, and answers a small set of test questions
using Gemini. No API registration or document download needed.

Usage:
    python -m test_mode.run_local_test
    # or from project root:
    python lucio_hackathon/test_mode/run_local_test.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

# Ensure the project root is on sys.path when run directly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import LOCAL_TEST_DOCS
from ingestion.parser import parse_documents
from index.bm25_index import build_index
from qa.gemini_answer import answer_all_questions


# ─── sample questions ─────────────────────────────────────────────────────────
# Override this list with your actual test questions.

SAMPLE_QUESTIONS = [
    {"id": 1, "question": "What is the main alternative to SUMO for academic research and how is it different?"},
    {"id": 2, "question": "Which location has the highest value in the Banking Transactions dataset?"},
    {"id": 3, "question": "Where and when was the KMIL Amendment executed?"},
    {"id": 4, "question": "In the Satyam College of Engineering, what is the subject taught on wednesdays between 10:20 and 11:10?"},
    {"id": 5, "question": "What was EBCs annual revenues form operations in the years from 2018-2021"},
    {"id": 6, "question": "Who are the book running leads for the Hyundai IPO?"},
    {"id": 7, "question": "Compare the aggregated amount raised by Mitsu Chem Plast, DeltaTech Gaming Ltd, First Meridian"},
    {"id": 8, "question": "Which sections of the Income Tax Act deal with taxation of prize money from online gaming and horse racing?"},
    {"id": 9, "question": "How many sexual harassment complaints were filed in the 22-23 FY in Paytm?"},
    {"id": 10, "question": "What is the Cravath Scale salary for attorneys from the class of 2018?"},
    {"id": 11, "question": "In the Cherabuddi Educational Society SLP, how many annexures are attached?"},
    {"id": 12, "question": "For Bikaji SSA, what is the stamp duty?"},
    {"id": 13, "question": "What is the stamp duty for DTD-29-03-2025-Final.pdf"},
    {"id": 14, "question": "When was Suzlon Energy Incorporated?"},
    {"id": 15, "question": "Who is the investigating officer assigned for the case in CHALAN--FIR NO-483-14 U-S-420,406-merged.pdf and what is his rank?"},
]


# ─── runner ───────────────────────────────────────────────────────────────────

def run_local_test(
    docs_folder: str | None = None,
    questions: list[dict] | None = None,
    max_docs: int = 200,
) -> list[dict]:
    """
    Run the full pipeline locally.

    Parameters
    ----------
    docs_folder : path to folder containing PDF files (defaults to LOCAL_TEST_DOCS)
    questions   : list of {id, question} dicts (defaults to SAMPLE_QUESTIONS)
    max_docs    : maximum number of PDFs to use (default 200)

    Returns
    -------
    List of answer dicts.
    """
    folder = docs_folder or LOCAL_TEST_DOCS
    questions = questions or SAMPLE_QUESTIONS

    # ── 1. discover PDFs ──────────────────────────────────────────────────────
    pdf_paths = sorted(glob.glob(os.path.join(folder, "**", "*.pdf"), recursive=True))
    if not pdf_paths:
        print(f"[local_test] No PDFs found in: {folder}", file=sys.stderr)
        print(
            "[local_test] Place PDF files in the sample_docs/ folder or pass docs_folder=",
            file=sys.stderr,
        )
        sys.exit(1)

    pdf_paths = pdf_paths[:max_docs]
    print(f"[local_test] Using {len(pdf_paths)} PDFs from {folder}")

    start = time.perf_counter()

    # ── 2. parse ──────────────────────────────────────────────────────────────
    pages = parse_documents(pdf_paths)

    # ── 3. index ──────────────────────────────────────────────────────────────
    index = build_index(pages)

    # ── 4. answer ─────────────────────────────────────────────────────────────
    results = answer_all_questions(questions, index)

    elapsed = time.perf_counter() - start
    print(f"\n[local_test] Completed in {elapsed:.2f}s")
    print(json.dumps(results, indent=2))
    return results


# ─── entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local test mode for Lucio Hackathon pipeline")
    parser.add_argument(
        "--docs", "-d",
        default=None,
        help="Path to folder with PDF files (default: test_mode/sample_docs/)",
    )
    parser.add_argument(
        "--max-docs", "-n",
        type=int, default=200,
        help="Maximum number of PDFs to use (default: 200)",
    )
    args = parser.parse_args()

    run_local_test(docs_folder=args.docs, max_docs=args.max_docs)
