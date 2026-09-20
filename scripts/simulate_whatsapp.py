"""Free local WhatsApp webhook simulator.

This avoids paid Twilio setup while exercising the same `/webhook/whatsapp`
FastAPI route that Twilio would call in production.

Usage:
    source .venv/bin/activate
    python scripts/simulate_whatsapp.py "PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?"
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

import src.api as api_module
from src.api import app


def _headers(data: dict) -> dict:
    if not api_module.TWILIO_AUTH_TOKEN:
        return {}
    # Mirror the server side parse_qsl behavior: blank values are dropped.
    params = {k: v for k, v in data.items() if str(v).strip()}
    validator = RequestValidator(api_module.TWILIO_AUTH_TOKEN)
    signature = validator.compute_signature("http://testserver/webhook/whatsapp", params)
    return {"X-Twilio-Signature": signature}


def main() -> int:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?"

    payload = {
        "Body": query,
        "From": "whatsapp:+910000000000",
        "ProfileName": "Demo Farmer",
    }

    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", data=payload, headers=_headers(payload))

    print(f"HTTP {response.status_code}")
    print(response.text)
    return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
