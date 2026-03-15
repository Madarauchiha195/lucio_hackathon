"""
main.py — End-to-end pipeline for the Lucio Hackathon.

MODE 1 (local test):   python main.py --mode local  [--docs PATH] [--max-docs N]
MODE 2 (hackathon):    python main.py --mode hackathon

The script orchestrates:
    1. Register team (hackathon mode only)
    2. Download 200 encrypted documents (hackathon) or load local PDFs (local)
    3. Parse PDFs page-by-page using PyMuPDF (parallel)
    4. Build BM25 search index
    5. Answer 15 questions with Gemini
    6. Submit answers (hackathon mode only)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time


# ─── ensure project root is on path ──────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ─── lazy imports (speed up startup for local mode) ──────────────────────────

def _import_all():
    """Import all heavy modules after argument parsing."""
    global register_team, fetch_doc_list, download_documents
    global parse_documents, build_index
    global answer_all_questions
    global submit_answers

    from api.register      import register_team
    from api.download_docs import fetch_doc_list, download_documents
    from api.submit        import submit_answers
    from ingestion.parser  import parse_documents
    from index.bm25_index  import build_index
    from qa.gemini_answer   import answer_all_questions


# ─── hackathon mode ───────────────────────────────────────────────────────────

def run_hackathon(questions_override: list[dict] | None = None) -> list[dict]:
    """
    Full hackathon pipeline:
      register → download (async) → parse (parallel) → index → answer → submit
    """
    t0 = time.perf_counter()

    # 1. Register
    reg = register_team()
    token    = reg.get("token", "")
    password = reg.get("password", None)

    # Questions may come from the registration response or be overridden
    questions: list[dict] = questions_override or reg.get("questions", [])
    if not questions:
        print("[main] WARNING: No questions found in registration response.")

    # 2. Fetch document list + download
    doc_list  = fetch_doc_list(token)
    pdf_paths = download_documents(doc_list, password=password, token=token)

    # 3. Parse
    pages = parse_documents(pdf_paths)

    # 4. Index
    index = build_index(pages)

    # 5. Answer
    answers = answer_all_questions(questions, index)

    elapsed = time.perf_counter() - t0
    print(f"\n[main] Pipeline finished in {elapsed:.2f}s")

    # 6. Submit
    result = submit_answers(answers, token=token)
    print(f"[main] Submission result: {result}")

    # 7. Persist answers locally
    out_path = os.path.join(_ROOT, "answers.json")
    with open(out_path, "w") as f:
        json.dump(answers, f, indent=2)
    print(f"[main] Answers written to {out_path}")

    return answers


# ─── local test mode ─────────────────────────────────────────────────────────

def run_local(
    docs_folder: str | None = None,
    max_docs: int = 20,
    questions: list[dict] | None = None,
) -> list[dict]:
    """
    Local pipeline:
      load PDFs → parse (parallel) → index → answer (Gemini)
    No registration or submission.
    """
    from test_mode.run_local_test import run_local_test
    return run_local_test(
        docs_folder=docs_folder,
        questions=questions,
        max_docs=max_docs,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Lucio Hackathon — end-to-end QA pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mode 1 — Local test with PDFs from a folder:
  python main.py --mode local --docs ./my_pdfs --max-docs 20

  # Mode 2 — Hackathon run:
  python main.py --mode hackathon
        """,
    )
    p.add_argument(
        "--mode", "-m",
        choices=["local", "hackathon"],
        default="local",
        help="Run mode: 'local' (test) or 'hackathon' (live submission). Default: local",
    )
    # Local mode options
    p.add_argument(
        "--docs", "-d",
        default=None,
        help="(local mode) Path to folder containing PDF files.",
    )
    p.add_argument(
        "--max-docs", "-n",
        type=int, default=20,
        help="(local mode) Maximum number of PDFs to process. Default: 20",
    )
    # Hackathon mode options
    p.add_argument(
        "--questions-file", "-q",
        default=None,
        help="(hackathon mode) Path to JSON file with questions [{id, question},...]. "
             "If omitted, questions are taken from the registration response.",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    _import_all()

    questions: list[dict] | None = None
    if args.questions_file:
        with open(args.questions_file) as f:
            questions = json.load(f)

    if args.mode == "hackathon":
        print("=" * 60)
        print("  MODE 2 — Hackathon Run")
        print("=" * 60)
        run_hackathon(questions_override=questions)

    else:  # local
        print("=" * 60)
        print("  MODE 1 — Local Test")
        print("=" * 60)
        run_local(docs_folder=args.docs, max_docs=args.max_docs, questions=questions)


if __name__ == "__main__":
    main()
