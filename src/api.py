"""
src/api.py — Phase 4 Backend API
FastAPI backend for AI Crop Advisory WhatsApp chatbot and Web interfaces.

Endpoints:
  • GET  /health              — Healthcheck & service status
  • POST /api/v1/advisory     — Structured JSON advisory for web/apps
  • POST /api/v1/weather      — District-level weather & PAU gate alerts
  • POST /webhook/whatsapp    — Twilio WhatsApp webhook handler (TwiML response)
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware


# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.rag_chain import CropAdvisoryRAGChain, RAGResponse
from src.weather import WeatherService, WeatherGateAssessment, PUNJAB_DISTRICTS

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

from contextlib import asynccontextmanager

# Global singleton chain & weather service (instantiated on startup)
chain: Optional[CropAdvisoryRAGChain] = None
weather_service: Optional[WeatherService] = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    global chain, weather_service
    print("🚀 Initializing Kisan Mitra RAG Chain and Weather Services...")
    chain = CropAdvisoryRAGChain()
    weather_service = WeatherService()
    print("🌾 Kisan Mitra Backend API Ready!")
    yield


app = FastAPI(
    title="🌾 Kisan Mitra — AI Crop Advisory API",
    description="PAU-grounded multilingual crop advisory backend with weather gating for Punjab farmers.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard (Phase 5 Streamlit / React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Phase 3: Twilio WhatsApp webhook security
# ---------------------------------------------------------------------------
# Load Twilio credentials from .env
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Validate Twilio request signature to prevent spoofed webhook calls.
# Only enforced when TWILIO_AUTH_TOKEN is set (skip in local dev).
def _validate_twilio_signature(request: Request, body: bytes) -> bool:
    """
    Verify the X-Twilio-Signature header using HMAC-SHA1.
    See: https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    if not TWILIO_AUTH_TOKEN:
        # Dev mode: auth token not set, skip validation
        return True
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        url = str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")
        # Parse body params for validation
        import urllib.parse
        params = dict(urllib.parse.parse_qsl(body.decode("utf-8")))
        return validator.validate(url, params, signature)
    except Exception:
        return False




# ---------------------------------------------------------------------------
# Pydantic Schemas for JSON APIs
# ---------------------------------------------------------------------------

class AdvisoryRequest(BaseModel):
    query: str = Field(..., examples=["PR 126 lagayi hai 25 din ho gaye, urea kab daalu?"])
    crop: Optional[str] = Field(None, examples=["paddy"])
    district: Optional[str] = Field("Ludhiana", examples=["Ludhiana"])
    language: Optional[str] = Field("auto", examples=["auto"])
    use_weather: bool = Field(True, description="Whether to apply real-time PAU weather gates")


class WeatherGateResponse(BaseModel):
    district: str
    rain_risk: str
    wind_risk: str
    irrigation_gate: str
    fertilizer_gate: str
    weather_summary: str


class AdvisoryResponse(BaseModel):
    success: bool
    query: str
    answer: str
    detected_crop: Optional[str]
    language_used: str
    district: str
    confidence: str
    sources: List[str]
    weather_gate: Optional[WeatherGateResponse] = None


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Verify system readiness, retriever connection, and active model."""
    return {
        "status": "healthy",
        "service": "kisan-mitra-crop-advisory",
        "model": chain.model if chain else "not_loaded",
        "collection_count": chain.retriever.collection.count() if chain else 0,
        "districts_supported": list(PUNJAB_DISTRICTS.keys()),
    }


@app.post("/api/v1/advisory", response_model=AdvisoryResponse)
def get_crop_advisory(req: AdvisoryRequest):
    """
    Standard JSON endpoint for web dashboard or mobile app.
    Takes farmer query and returns grounded PAU recommendations + weather gates.
    """
    if not chain:
        raise HTTPException(status_code=503, detail="RAG Chain service not initialized")

    try:
        resp: RAGResponse = chain.query(
            farmer_query=req.query,
            crop_hint=req.crop,
            language=req.language or "auto",
            district=req.district,
            use_weather=req.use_weather,
        )

        weather_gate_dict = None
        if resp.weather_gate:
            weather_gate_dict = WeatherGateResponse(
                district=resp.weather_gate.district,
                rain_risk=resp.weather_gate.rain_risk,
                wind_risk=resp.weather_gate.wind_risk,
                irrigation_gate=resp.weather_gate.irrigation_gate,
                fertilizer_gate=resp.weather_gate.fertilizer_gate,
                weather_summary=resp.weather_gate.weather_summary_text,
            )

        return AdvisoryResponse(
            success=True,
            query=resp.query,
            answer=resp.answer,
            detected_crop=resp.detected_crop,
            language_used=resp.language_used,
            district=resp.district,
            confidence=resp.confidence,
            sources=resp.sources,
            weather_gate=weather_gate_dict,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory generation failed: {str(e)}")


@app.post("/api/v1/weather", response_model=WeatherGateResponse)
def get_district_weather(district: str = "Ludhiana", crop: Optional[str] = None):
    """Get live weather and PAU weather gate warnings for any Punjab district."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not initialized")

    weather_data = weather_service.get_weather(district)
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"Weather data unavailable for {district}")

    gate = weather_service.evaluate_gates(weather_data, crop=crop)
    return WeatherGateResponse(
        district=gate.district,
        rain_risk=gate.rain_risk,
        wind_risk=gate.wind_risk,
        irrigation_gate=gate.irrigation_gate,
        fertilizer_gate=gate.fertilizer_gate,
        weather_summary=gate.weather_summary_text,
    )


# ---------------------------------------------------------------------------
# WhatsApp Webhook (Twilio) with Multi-Turn Memory
# ---------------------------------------------------------------------------

from src.session_manager import session_manager

RESET_KEYWORDS = {"reset", "restart", "shuru", "ਸ਼ੁਰੂ", "ਨਵਾਂ ਸਵਾਲ", "नया सवाल", "clear"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp Webhook with Multi-Turn Memory.
    Receives incoming WhatsApp message payload from Twilio, preserves conversation
    history across turns, and responds with TwiML XML.

    Security: Validates Twilio X-Twilio-Signature header (HMAC-SHA1).
    """
    # Read raw body before form parsing so Twilio signature validation works.
    raw_body = await request.body()
    if not _validate_twilio_signature(request, raw_body):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    form = await request.form()
    Body = form.get("Body")
    From = form.get("From")
    ProfileName = form.get("ProfileName")
    sender = str(From or "anonymous_farmer")

    if not Body or not str(Body).strip():
        twiml_empty = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<Response>\n"
            "  <Message>ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ / नमस्ते! ਕਿਸਾਨ ਮਿੱਤਰ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ।\n"
            "Please send your crop question or variety name.\n"
            "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀ ਫਸਲ ਜਾਂ ਖਾਦ/ਪਾਣੀ ਬਾਰੇ ਸਵਾਲ ਪੁੱਛੋ।</Message>\n"
            "</Response>"
        )
        return Response(content=twiml_empty, media_type="application/xml")

    query_text = str(Body).strip()

    # Check for session reset
    if query_text.lower() in RESET_KEYWORDS:
        session_manager.reset(sender)
        twiml_reset = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<Response>\n"
            "  <Message>✅ ਪੁਰਾਣੀ ਗੱਲਬਾਤ ਰੀਸੈੱਟ ਹੋ ਗਈ ਹੈ।\n"
            "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣਾ ਨਵਾਂ ਸਵਾਲ ਪੁੱਛੋ। (Conversation reset. What can I help with?)</Message>\n"
            "</Response>"
        )
        return Response(content=twiml_reset, media_type="application/xml")

    # Retrieve or initialize farmer session
    session = session_manager.get_or_create(sender, profile_name=ProfileName)
    session.add_turn("farmer", query_text)

    # Use prior crop/district context if not explicitly mentioned in current message
    crop_hint = session.crop
    district_hint = session.district or "Ludhiana"

    print(f"📩 WhatsApp Message from {ProfileName or sender} [{district_hint}, {crop_hint or 'no crop'}]: {query_text}")

    # Generate answer via RAG chain
    try:
        resp = chain.query(
            farmer_query=query_text,
            crop_hint=crop_hint,
            district=district_hint,
            language="auto",
            use_weather=True,
        )
        answer_text = resp.answer

        # Update session with newly detected crop or district
        session_manager.update_profile(
            session,
            crop=resp.detected_crop or session.crop,
            district=resp.district or session.district,
        )
        session.add_turn("kisan_mitra", answer_text)

    except Exception as e:
        print(f"❌ Error generating WhatsApp reply: {e}")
        answer_text = (
            "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ। ਤਕਨੀਕੀ ਖ਼ਰਾਬੀ ਕਾਰਨ ਜਵਾਬ ਨਹੀਂ ਮਿਲ ਸਕਿਆ। "
            "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਨਜ਼ਦੀਕੀ KVK ਨਾਲ ਸੰਪਰਕ ਕਰੋ।\n\n"
            "Technical error occurred. Please consult your local KVK."
        )

    # Sanitize special XML characters (&, <, >)
    safe_answer = (
        answer_text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    twiml_response = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f"  <Message>{safe_answer}</Message>\n"
        "</Response>"
    )

    return Response(content=twiml_response, media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False)
