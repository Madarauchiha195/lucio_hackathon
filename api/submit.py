"""
api/submit.py — Submit final answers to the hackathon judging endpoint.
"""

import sys
import requests
from config import API_BASE_URL


def submit_answers(answers: list[dict], token: str) -> dict:
    """
    POST /submit  with the answers payload.

    Parameters
    ----------
    answers : list of {question_id, answer, document, page}
    token   : bearer token from registration

    Returns
    -------
    Response JSON (score, feedback, etc.)
    """
    url = f"{API_BASE_URL}/submit"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"answers": answers}

    print(f"[submit] Submitting {len(answers)} answers to {url} …")
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[submit] ERROR: {exc}", file=sys.stderr)
        raise

    result = resp.json()
    print(f"[submit] Response: {result}")
    return result
