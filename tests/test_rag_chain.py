"""
tests/test_rag_chain.py
Comprehensive test suite for Phase 2 Step 5 (src/rag_chain.py).
Tests:
- Unit tests: Crop detection, Language detection, Prompt builder
- Integration tests: End-to-end RAG queries (English, Hindi, Punjabi)
- Safety tests: KVK safety disclaimer, Hallucination/Out-of-scope fallback
- Streaming test: query_stream generator output
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.rag_chain import (
    CropAdvisoryRAGChain,
    RAGResponse,
    SAFETY_DISCLAIMER,
    _detect_crop,
    _detect_language,
    _language_instruction,
)


# ---------------------------------------------------------------------------
# Unit Tests: Crop Detection & Language Routing
# ---------------------------------------------------------------------------

class TestDetectionHelpers:
    """Test rule-based crop & language detection functions."""

    def test_detect_crop_paddy_variations(self):
        assert _detect_crop("When to apply urea in PR 126?") == "paddy"
        assert _detect_crop("dhan me paani kab lagayein?") == "paddy"
        assert _detect_crop("ਝੋਨੇ ਨੂੰ ਪਾਣੀ ਕਦੋਂ ਦੇਣਾ ਹੈ?") == "paddy"
        assert _detect_crop("jeeri di variety PR 128") == "paddy"

    def test_detect_crop_wheat_variations(self):
        assert _detect_crop("Wheat CRI stage irrigation schedule") == "wheat"
        assert _detect_crop("ਕਣਕ ਵਿੱਚ ਪੀਲੀ ਕੁੰਗੀ ਦੀ ਰੋਕਥਾਮ") == "wheat"
        assert _detect_crop("gehun me pehla paani kab de") == "wheat"

    def test_detect_crop_rotation_both_crops(self):
        # When both crops are mentioned, should return None to avoid strict single-crop filtering
        res = _detect_crop("ਝੋਨੇ ਵਿੱਚ DAP ਪਾਉਣੀ ਚਾਹੀਦੀ ਹੈ ਜੇ ਕਣਕ ਵਿੱਚ ਪਾਈ ਸੀ?")
        assert res is None, "Rotation query with both crops should allow cross-crop retrieval"

    def test_detect_crop_unknown(self):
        assert _detect_crop("What is the weather today?") is None

    def test_detect_language_punjabi(self):
        assert _detect_language("ਕਣਕ ਨੂੰ ਪਾਣੀ ਕਦੋਂ ਦੇਣਾ ਹੈ?") == "punjabi"
        assert _detect_language("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਕਿਸਾਨ ਵੀਰੋ") == "punjabi"

    def test_detect_language_hindi(self):
        assert _detect_language("धान में यूरिया कब डालना चाहिए?") == "hindi"
        assert _detect_language("पहला पानी कब लगाएं?") == "hindi"

    def test_detect_language_hinglish(self):
        assert _detect_language("dhan me urea kab aur kitna daalna chahiye?") == "hindi"
        assert _detect_language("gehun me paani kab lagana hai?") == "hindi"

    def test_detect_language_english(self):
        assert _detect_language("When should I irrigate wheat crop?") == "english"
        assert _detect_language("What are the recommended varieties?") == "english"


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End RAG Chain with Gemini
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rag_chain():
    """Shared instance of CropAdvisoryRAGChain across test suite."""
    return CropAdvisoryRAGChain(temperature=0.1)


class TestRAGChainIntegration:
    """Live API integration tests connecting ChromaDB to Gemini."""

    def test_chain_initialization(self, rag_chain):
        assert rag_chain.model == "gemini-3.5-flash-lite"
        assert rag_chain.top_k == 3
        assert rag_chain.client is not None
        assert rag_chain.retriever is not None

    def test_paddy_query_grounding(self, rag_chain):
        """Test paddy urea query produces grounded answer with sources and disclaimer."""
        query = "PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?"
        resp = rag_chain.query(query)

        assert isinstance(resp, RAGResponse)
        assert resp.detected_crop == "paddy"
        assert len(resp.retrieved_chunks) > 0
        assert len(resp.sources) > 0

        # Safety disclaimer must be present
        assert "KVK" in resp.answer
        assert "Krishi Vigyan Kendra" in resp.answer

        # Agronomic correctness: PR 126 cutoff is 35 days in PAU
        assert "35" in resp.answer or "35 दिन" in resp.answer or "PR 126" in resp.answer

    def test_wheat_query_grounding(self, rag_chain):
        """Test wheat first irrigation inquiry (CRI stage)."""
        query = "Wheat crop me pehla paani kab lagana chahiye?"
        resp = rag_chain.query(query)

        assert isinstance(resp, RAGResponse)
        assert resp.detected_crop == "wheat"
        assert len(resp.retrieved_chunks) > 0
        assert "KVK" in resp.answer

        # Agronomic correctness: CRI stage is 20-25 days / Crown Root Initiation
        answer_lower = resp.answer.lower()
        assert ("20" in answer_lower or "25" in answer_lower or "cri" in answer_lower or "crown root" in answer_lower)

    def test_english_query_returns_english(self, rag_chain):
        """Test English query receives English response with disclaimer."""
        query = "Should I stop irrigating paddy before harvesting?"
        resp = rag_chain.query(query, language="english")

        assert isinstance(resp, RAGResponse)
        assert resp.language_used == "english"
        assert "15 days" in resp.answer.lower() or "stop" in resp.answer.lower()
        assert "KVK" in resp.answer

    def test_punjabi_query_returns_gurmukhi(self, rag_chain):
        """Test Punjabi query returns response in Gurmukhi script."""
        query = "ਕਣਕ ਵਿੱਚ ਪਹਿਲਾ ਪਾਣੀ ਕਦੋਂ ਲਾਈਏ?"
        resp = rag_chain.query(query)

        assert isinstance(resp, RAGResponse)
        # Check Gurmukhi script characters exist in response
        has_gurmukhi = any('\u0A00' <= char <= '\u0A7F' for char in resp.answer)
        assert has_gurmukhi, "Response to Punjabi query should contain Gurmukhi text"
        assert "KVK" in resp.answer or "ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ" in resp.answer

    def test_out_of_scope_or_unknown_query(self, rag_chain):
        """Test query outside PAU knowledge base (e.g. apple farming in Ludhiana or crypto) refers to KVK."""
        query = "How to grow apple trees in Ludhiana Punjab?"
        resp = rag_chain.query(query)

        assert isinstance(resp, RAGResponse)
        # Either fallback or Gemini directly clarifies lack of PAU data and points to KVK
        assert "KVK" in resp.answer or "Krishi Vigyan Kendra" in resp.answer

    def test_streaming_query(self, rag_chain):
        """Test query_stream generates text chunks and appends disclaimer."""
        query = "When to apply first irrigation in wheat?"
        chunks = list(rag_chain.query_stream(query))

        assert len(chunks) > 1, "Streaming should return multiple chunks"
        full_streamed_text = "".join(chunks)
        assert len(full_streamed_text) > 50
        assert "KVK" in full_streamed_text
        assert "Krishi Vigyan Kendra" in full_streamed_text

    def test_query_with_live_weather_integration(self, rag_chain):
        """Test query seamlessly incorporates live Open-Meteo weather and PAU weather gate."""
        query = "Ludhiana me wheat crop me paani lagana hai ya rukna chahiye?"
        resp = rag_chain.query(query, district="Ludhiana", use_weather=True)

        assert isinstance(resp, RAGResponse)
        assert resp.district == "Ludhiana"
        assert resp.weather_gate is not None
        assert resp.weather_gate.district == "Ludhiana"
        assert resp.weather_gate.rain_risk in ["none", "moderate", "high"]
        assert resp.weather_gate.wind_risk in ["safe", "advisory", "high_risk"]
        assert len(resp.weather_gate.weather_summary_text) > 50
        assert "KVK" in resp.answer


class TestWeatherServiceUnits:
    """Unit tests for WeatherService and PAU weather gate evaluator."""

    def test_resolve_district_default(self):
        from src.weather import WeatherService
        ws = WeatherService()
        dist, lat, lon = ws.resolve_district("how to irrigate paddy?")
        assert dist == "Ludhiana"
        assert round(lat, 2) == 30.90

    def test_resolve_district_explicit(self):
        from src.weather import WeatherService
        ws = WeatherService()
        dist, lat, lon = ws.resolve_district("Bathinda me kanak me paani")
        assert dist == "Bathinda"
        assert round(lat, 2) == 30.21

    def test_live_weather_fetch(self):
        from src.weather import WeatherService
        ws = WeatherService()
        data = ws.get_weather("Ludhiana")
        assert data is not None
        assert data.district == "Ludhiana"
        assert -10 < data.temperature_c < 60
        assert 0 <= data.humidity_pct <= 100

    def test_weather_gate_rain_logic(self):
        from src.weather import WeatherService, WeatherData
        import time
        ws = WeatherService()
        # Mock high rain event
        mock_rainy = WeatherData(
            district="Ludhiana",
            latitude=30.90,
            longitude=75.85,
            temperature_c=25.0,
            humidity_pct=85,
            current_rain_mm=2.0,
            current_wind_kmh=8.0,
            total_rain_next_48h_mm=22.0,
            max_rain_probability_48h=90,
            max_wind_next_48h_kmh=10.0,
            timestamp=time.time(),
        )
        gate = ws.evaluate_gates(mock_rainy, crop="wheat")
        assert gate.rain_risk == "high"
        assert "WITHHOLD" in gate.irrigation_gate
        assert "DO NOT apply" in gate.fertilizer_gate

