"""
api/register.py — Register the team and retrieve auth token + corpus password.
"""

import requests
import sys
from config import API_BASE_URL, TEAM_NAME, TEAM_EMAIL


def register_team() -> dict:
    """
    POST /register  →  { token, password, question_ids, ... }
    Returns the full registration payload dict.
    """
    url = f"{API_BASE_URL}/register"
    payload = {
        "team_name": TEAM_NAME,
        "email": TEAM_EMAIL,
    }

    print(f"[register] Registering team '{TEAM_NAME}' at {url} …")
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[register] ERROR: {exc}", file=sys.stderr)
        raise

    data = resp.json()
    print(f"[register] Success. Token: {data.get('token', '?')[:8]}…")
    return data
