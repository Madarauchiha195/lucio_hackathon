"""
config.py — Central configuration for Lucio Hackathon system.
Update API_BASE_URL, TEAM_NAME, GEMINI_API_KEY before running.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ─── API ──────────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("HACKATHON_API_URL", "https://hackathon.lucio.ai")  # override via env
TEAM_NAME    = os.getenv("HACKATHON_TEAM_NAME", "TeamLucio")
TEAM_EMAIL   = os.getenv("HACKATHON_TEAM_EMAIL", "team@lucio.ai")

# ─── Gemini ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_MODEL     = "gemini-2.5-flash"          # fast and cheap
GEMINI_TEMP      = 0.0                          # deterministic answers

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR          = os.path.join(BASE_DIR, "data")
DOCS_DIR          = os.path.join(DATA_DIR, "documents")      # downloaded / local PDFs
LOCAL_TEST_DOCS   = os.path.join(BASE_DIR, "test_mode", "sample_docs")  # 20 sample PDFs

# ─── BM25 ─────────────────────────────────────────────────────────────────────
BM25_TOP_K = 5       # pages returned per query

# ─── Performance ──────────────────────────────────────────────────────────────
DOWNLOAD_CONCURRENCY = 20   # simultaneous async downloads
PARSE_WORKERS        = 8    # parallel PDF parse workers

# ─── Hackathon ────────────────────────────────────────────────────────────────
NUM_DOCS      = 200
NUM_QUESTIONS = 15
