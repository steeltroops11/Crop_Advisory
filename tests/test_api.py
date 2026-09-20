"""
tests/test_api.py
Integration tests for FastAPI backend (src/api.py).
Tests:
- GET /health
- POST /api/v1/weather
- POST /api/v1/advisory
- POST /webhook/whatsapp (Twilio format)
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import src.api as api_module
from src.api import app


def _twilio_headers(data: dict) -> dict:
    """Sign local TestClient webhook requests when Twilio auth is enabled."""
    if not api_module.TWILIO_AUTH_TOKEN:
        return {}
    from twilio.request_validator import RequestValidator

    # Mirror the server side parse_qsl behavior: blank values are dropped.
    params = {k: v for k, v in data.items() if str(v).strip()}
    validator = RequestValidator(api_module.TWILIO_AUTH_TOKEN)
    signature = validator.compute_signature(
        "http://testserver/webhook/whatsapp",
        params,
    )
    return {"X-Twilio-Signature": signature}



def _post_whatsapp(client: TestClient, data: dict):
    return client.post("/webhook/whatsapp", data=data, headers=_twilio_headers(data))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "kisan-mitra-crop-advisory"
    assert data["collection_count"] > 0
    assert "ludhiana" in data["districts_supported"]


def test_weather_endpoint(client):
    response = client.post("/api/v1/weather?district=Ludhiana")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Ludhiana"
    assert data["rain_risk"] in ["none", "moderate", "high"]
    assert data["wind_risk"] in ["safe", "advisory", "high_risk"]
    assert len(data["weather_summary"]) > 20


def test_advisory_endpoint_paddy(client):
    payload = {
        "query": "PR 126 lagayi hai, urea kab daalein?",
        "district": "Ludhiana",
        "crop": "paddy",
        "use_weather": True,
    }
    response = client.post("/api/v1/advisory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detected_crop"] == "paddy"
    assert "KVK" in data["answer"]
    assert len(data["sources"]) > 0
    assert data["weather_gate"] is not None


def test_whatsapp_webhook_empty_body(client):
    response = _post_whatsapp(client, {"Body": "", "From": "+919876543210"})
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "<Message>" in response.text


def test_whatsapp_webhook_query(client):
    response = _post_whatsapp(
        client,
        {
            "Body": "Wheat crop me pehla paani kab lagayein?",
            "From": "whatsapp:+919876543210",
            "ProfileName": "Gurpreet Singh",
        },
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "<Message>" in response.text
    assert "KVK" in response.text


def test_whatsapp_multi_turn_and_reset(client):
    phone = "whatsapp:+919812345678"

    # Turn 1: State crop & variety
    r1 = _post_whatsapp(
        client,
        {"Body": "Mera khet Ludhiana me hai aur maine PR 126 paddy lagayi hai.", "From": phone},
    )
    assert r1.status_code == 200

    # Turn 2: Follow-up question WITHOUT mentioning crop name again
    r2 = _post_whatsapp(
        client,
        {"Body": "Isme urea kab tak poori karni hai?", "From": phone},
    )
    assert r2.status_code == 200
    # Agronomic fact: PR 126 cutoff is 35 days
    assert "35" in r2.text or "PR 126" in r2.text or "यूरिया" in r2.text

    # Turn 3: Reset session
    r3 = _post_whatsapp(
        client,
        {"Body": "reset", "From": phone},
    )
    assert r3.status_code == 200
    assert "ਰੀਸੈੱਟ" in r3.text or "reset" in r3.text.lower()

