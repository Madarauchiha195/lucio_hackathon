"""
qa/gemini_answer.py — Use Gemini to answer a question given retrieved context.

The model is instructed to return exactly:
    Answer:   <text>
    Document: <filename>
    Page:     <number>
"""

from __future__ import annotations

import re
import sys

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMP


# ─── initialise Gemini once ───────────────────────────────────────────────────

client = genai.Client(api_key=GEMINI_API_KEY)


# ─── prompt template ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a legal document assistant.

Answer the question using ONLY the provided context.

Return your response in EXACTLY this format (no extra text, no markdown):
Answer: <your concise answer>
Document: <exact document filename>
Page: <page number as integer>

If the answer cannot be found in the context, respond with:
Answer: Not Found
Document: Not Found
Page: 0
"""

_USER_TEMPLATE = """\
Context:
{context}

Question: {question}
"""


# ─── parsing helpers ─────────────────────────────────────────────────────────

def _parse_response(raw: str) -> tuple[str, str, int]:
    """Extract answer, document, page from the model's raw text output."""
    answer   = "Not Found"
    document = "Not Found"
    page     = 0

    for line in raw.splitlines():
        line = line.strip()
        if line.lower().startswith("answer:"):
            answer = line.split(":", 1)[1].strip()
        elif line.lower().startswith("document:"):
            document = line.split(":", 1)[1].strip()
        elif line.lower().startswith("page:"):
            raw_page = line.split(":", 1)[1].strip()
            try:
                page = int(re.sub(r"[^\d]", "", raw_page) or "0")
            except ValueError:
                page = 0

    return answer, document, page


# ─── main API ─────────────────────────────────────────────────────────────────

def answer_question(
    question: str,
    context: str,
    question_id: str | int = 0,
) -> dict:
    """
    Call Gemini with the question + context and parse the structured response.

    Returns
    -------
    {
        "question_id": ...,
        "answer":      str,
        "document":    str,
        "page":        int,
    }
    """
    prompt = _USER_TEMPLATE.format(context=context, question=question)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[_SYSTEM_PROMPT, prompt],
            config=types.GenerateContentConfig(temperature=GEMINI_TEMP),
        )
        raw_text = response.text
    except Exception as exc:
        print(f"[gemini] ERROR for question {question_id}: {exc}", file=sys.stderr)
        raw_text = ""

    answer, document, page = _parse_response(raw_text)
    return {
        "question_id": question_id,
        "answer":      answer,
        "document":    document,
        "page":        page,
    }


def answer_all_questions(
    questions: list[dict],
    index,
    top_k: int = 5,
) -> list[dict]:
    """
    Answer a list of questions sequentially (Gemini free tier has rate limits).

    Parameters
    ----------
    questions : list of {"id": ..., "question": str} dicts
    index     : BM25Index instance
    top_k     : pages to retrieve per question

    Returns
    -------
    List of answer dicts.
    """
    from qa.retriever import retrieve, build_context

    results = []
    for q in questions:
        qid  = q.get("id", q.get("question_id", len(results)))
        text = q.get("question", q.get("text", ""))

        pages   = retrieve(text, index, top_k=top_k)
        context = build_context(pages)
        result  = answer_question(text, context, question_id=qid)
        results.append(result)
        print(
            f"[gemini] Q{qid}: {result['answer'][:80]} "
            f"| doc={result['document']} p={result['page']}"
        )

    return results
