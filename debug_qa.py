import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ingestion.parser import parse_documents
from index.bm25_index import build_index
from qa.retriever import retrieve, build_context
from qa.gemini_answer import answer_question
from dotenv import load_dotenv

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# take just 1 pdf for quick test
pages = parse_documents(["test_mode/sample_docs/income-tax-act-1961-amended-by-finance-no.-2-act-2024 (1).pdf"])
index = build_index(pages)
q = "Which sections of the Income Tax Act deal with taxation of prize money from online gaming and horse racing?"
pages_retrieved = retrieve(q, index, top_k=5)

print("--- RETRIEVED PAGES ---")
for p in pages_retrieved:
    print(f"Doc: {p['document_name']} Page: {p['page_number']} Score: {p.get('score')}")

ctx = build_context(pages_retrieved)
print("\n--- CONTEXT ---")
print(ctx[:1000] + "...\n")

print("--- ANSWER ---")
ans = answer_question(q, ctx, question_id=1)
print(ans)
