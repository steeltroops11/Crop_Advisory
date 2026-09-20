"""
rag_chain.py — Phase 2, Step 5
AI Crop Advisory for Small Farmers (Punjab)

Connects ChromaDB retrieval to Gemini LLM with:
  • Strict PAU grounding (no hallucination)
  • Safety disclaimer on every response
  • Multilingual output: English / Hindi / Punjabi
  • Structured RAGResponse with source attribution
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal

# ── Project root on sys.path ────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import GEMINI_API_KEY
from src.retriever import CropKnowledgeRetriever
from src.weather import WeatherService, WeatherGateAssessment

# ── New google-genai SDK ─────────────────────────────────────────────────────
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Best balance of speed, cost, and multilingual quality for production.
# Verified available on this API key as of 2026-09:
#   gemini-3.5-flash-lite  ← primary (fast, cheap)
#   gemini-3.1-flash-lite  ← alternative fallback
GEMINI_MODEL = "gemini-3.5-flash-lite"

# Languages the system can respond in
Language = Literal["english", "hindi", "punjabi", "auto"]

# How many PAU context chunks to retrieve per query
DEFAULT_TOP_K = 3

# Safety disclaimer appended to every answer (trilingual)
SAFETY_DISCLAIMER = (
    "\n\n---\n"
    "⚠️ *यह AI-जनित सलाह है। महत्वपूर्ण निर्णयों के लिए अपने स्थानीय KVK "
    "(ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ / Krishi Vigyan Kendra) से ਸੰਪਰਕ ਕਰੋ।*\n"
    "⚠️ *This is AI-generated advice. For critical decisions, consult your "
    "local KVK (Krishi Vigyan Kendra).*"
)

# KVK fallback response when retrieval yields nothing relevant
KVK_FALLBACK_EN = (
    "I'm sorry, I couldn't find specific PAU guidelines for your question in "
    "my knowledge base. Please consult your local Krishi Vigyan Kendra (KVK) "
    "for accurate advice." + SAFETY_DISCLAIMER
)

# ---------------------------------------------------------------------------
# System prompt template — injected once per Gemini session
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are "Kisan Mitra" (ਕਿਸਾਨ ਮਿੱਤਰ / किसान मित्र), an expert AI crop advisory assistant
serving small farmers in Punjab, India. You provide agronomic guidance strictly
based on Punjab Agricultural University (PAU) Package of Practices.

## Core Rules (NEVER violate these)

1. **Strict Grounding**: Answer ONLY from the provided PAU context chunks.
   If the context does not contain the answer, say clearly:
   "I don't have enough PAU data for this. Please consult your local KVK."
   Never fabricate doses, timing, or chemical names.

2. **No Hallucination**: Do NOT invent varieties, pesticide doses, or schedules
   not present in the retrieved context. If context is partially relevant, use
   only the parts that directly apply.

3. **Multilingual Response**:
   - Detect the farmer's input language automatically.
   - If the query is in Punjabi (ਪੰਜਾਬੀ / Gurmukhi script), reply in Punjabi.
   - If the query is in Hindi or Hinglish, reply in Hindi.
   - If the query is in English, reply in English.
   - If the user explicitly requests a language, always honour that request.

4. **Farmer-Friendly Tone**: Use simple, practical language. Avoid jargon.
   When writing Punjabi, use Gurmukhi script. For Hindi, use Devanagari.

5. **Structure your answer** clearly:
   - Start with a direct 1-2 sentence answer.
   - Then give step-by-step actionable guidance from the PAU context.
   - End with the source chunk title/ID in a "📚 Source" line.

6. **Critical Safety**: If a farmer asks about pesticide/chemical doses or
   disease control measures, always add: "Confirm with your local KVK before
   applying any chemical."

7. **Crop & Stage Awareness**: Cross-reference the crop, variety, and growth
   stage mentioned by the farmer with the retrieved context. If they don't
   match, mention the mismatch explicitly.

8. **Weather-Gate Adherence**: When real-time weather and PAU weather gates are
   provided, cross-check them against irrigation or fertilizer decisions:
   - If rain is forecasted in 24-48h, explicitly advise withholding irrigation and urea top-dressing.
   - If high winds (>12-15 km/h) are forecasted, warn against irrigating standing wheat to prevent plant lodging (ਗਿਰਨਾ / ਡਿੱਗਣਾ).
"""

# ---------------------------------------------------------------------------
# Per-query user prompt template
# ---------------------------------------------------------------------------

def _build_user_prompt(
    query: str,
    context_chunks: List[Dict[str, Any]],
    language_instruction: str,
    weather_context: Optional[str] = None,
) -> str:
    """Build the RAG prompt with retrieved PAU chunks & weather gates injected as context."""
    if not context_chunks:
        return (
            f"Farmer's question: {query}\n\n"
            "No relevant PAU context was found. Politely tell the farmer you "
            "cannot find specific guidelines and direct them to their local KVK."
        )

    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        meta = chunk.get("metadata", {})
        context_text += (
            f"\n--- PAU Context Chunk {i} ---\n"
            f"ID: {chunk.get('id', 'unknown')}\n"
            f"Crop: {meta.get('crop', '')} | Stage: {meta.get('growth_stage', '')} | "
            f"Category: {meta.get('category', '')}\n"
            f"Title: {meta.get('title', '')}\n"
            f"Content:\n{chunk.get('content', '')}\n"
            f"Source: {meta.get('source', '')}\n"
        )

    weather_section = f"\n{weather_context}\n" if weather_context else ""

    return f"""FARMER'S QUESTION:
{query}

{language_instruction}
{weather_section}
RETRIEVED PAU KNOWLEDGE BASE CONTEXT:
{context_text}

INSTRUCTIONS:
- Answer the farmer's question using ONLY the PAU context provided above.
- If real-time weather gates are provided, integrate them into the practical advice (e.g. holding irrigation or fertilizer if rain/wind is coming).
- Be specific, practical, and farmer-friendly.
- If the context does not contain a direct answer, say so honestly and refer to KVK.
- Include a "📚 Source:" line at the end citing the PAU chunk ID(s) used.
"""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    """A single retrieved PAU knowledge chunk."""
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float


@dataclass
class RAGResponse:
    """Full structured response from the RAG chain."""
    answer: str                           # Final answer with disclaimer
    answer_core: str                      # Answer before disclaimer is appended
    query: str                            # Original farmer query
    detected_crop: Optional[str]          # Crop detected from query/context
    language_used: str                    # Language of response
    district: str = "Ludhiana"            # District used for weather localization
    weather_gate: Optional[WeatherGateAssessment] = None  # Live PAU weather gate
    retrieved_chunks: List[RetrievedChunk] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)   # Chunk IDs used
    confidence: str = "high"             # high / medium / low / fallback
    raw_llm_output: str = ""             # Raw LLM text before post-processing



# ---------------------------------------------------------------------------
# Crop & language detection helpers
# ---------------------------------------------------------------------------

# Simple keyword sets for fast crop detection from query text
_PADDY_KEYWORDS = {
    "paddy", "rice", "dhan", "jhona", "jhone", "ਝੋਨਾ", "ਝੋਨੇ", "ਧਾਨ", "ਜੀਰੀ", "ਪਰਮਲ",
    "pr 126", "pr126", "pr 121", "pr 128", "pr 130",
    "transplant", "puddled",
}
_WHEAT_KEYWORDS = {
    "wheat", "kanak", "gehun", "gehu", "ਕਣਕ", "ਕਣਕਾਂ", "ਗੇਹੂੰ", "गेहूं",
    "hd 3086", "pbd 0228", "wh 1105", "pk 0307", "cri stage",
    "yellow rust", "peeli kungi", "ਪੀਲੀ ਕੁੰਗੀ",
}
_GURMUKHI_RANGE = re.compile(r"[\u0A00-\u0A7F]")
_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")


def _detect_crop(query: str) -> Optional[str]:
    """
    Return 'paddy', 'wheat', or None based on keyword matching.
    If both crops are mentioned (e.g. rotation/carryover questions),
    returns None to avoid filtering out relevant cross-crop guidance.
    """
    q_lower = query.lower()
    is_paddy = any(kw in q_lower for kw in _PADDY_KEYWORDS)
    is_wheat = any(kw in q_lower for kw in _WHEAT_KEYWORDS)

    if is_paddy and is_wheat:
        return None  # Allow cross-crop retrieval (e.g., paddy-wheat rotation DAP rule)
    if is_paddy:
        return "paddy"
    if is_wheat:
        return "wheat"
    return None


def _detect_language(query: str) -> str:
    """Heuristic language detection from script ranges."""
    if _GURMUKHI_RANGE.search(query):
        return "punjabi"
    if _DEVANAGARI_RANGE.search(query):
        return "hindi"
    # Hinglish / Roman Hindi cues
    hinglish_cues = ["kab", "kitna", "kya", "mujhe", "hain", "dena", "chahiye",
                     "lagana", "daalna", "paani", "pani", "urea", "dhan", "kanak"]
    q_lower = query.lower()
    if sum(1 for cue in hinglish_cues if cue in q_lower) >= 2:
        return "hindi"
    return "english"


def _language_instruction(language: Language, auto_detected: str) -> str:
    """Return a clear language instruction to embed in the prompt."""
    effective = auto_detected if language == "auto" else language
    instructions = {
        "punjabi": (
            "🗣️ LANGUAGE INSTRUCTION: Reply in Punjabi using Gurmukhi script (ਪੰਜਾਬੀ). "
            "Use simple, rural Punjabi that a small farmer in Punjab can easily understand."
        ),
        "hindi": (
            "🗣️ LANGUAGE INSTRUCTION: Reply in Hindi using Devanagari script (हिन्दी). "
            "Use simple Hindi/Hinglish that a rural farmer can understand."
        ),
        "english": (
            "🗣️ LANGUAGE INSTRUCTION: Reply in clear, simple English suitable for "
            "a farmer with basic English literacy."
        ),
    }
    return instructions.get(effective, instructions["english"])


# ---------------------------------------------------------------------------
# Main RAG Chain class
# ---------------------------------------------------------------------------

class CropAdvisoryRAGChain:
    """
    Phase 2 RAG Chain — connects ChromaDB retrieval to Gemini LLM.

    Usage:
        chain = CropAdvisoryRAGChain()
        response = chain.query("PR 126 lagayi hai, urea kab daalu?")
        print(response.answer)
    """

    def __init__(
        self,
        model: str = GEMINI_MODEL,
        top_k: int = DEFAULT_TOP_K,
        temperature: float = 0.2,
        add_disclaimer: bool = True,
    ):
        """
        Args:
            model: Gemini model ID to use.
            top_k: Number of PAU context chunks to retrieve per query.
            temperature: LLM temperature (low = more grounded/deterministic).
            add_disclaimer: Whether to append the safety disclaimer to answers.
        """
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. Check your .env file."
            )

        self.model = model
        self.top_k = top_k
        self.temperature = temperature
        self.add_disclaimer = add_disclaimer

        # Initialise Gemini client (new google-genai SDK)
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # Initialise ChromaDB retriever
        self.retriever = CropKnowledgeRetriever()

        # Initialise Open-Meteo Weather & PAU Gate Service
        self.weather_service = WeatherService()

        print(f"✅ CropAdvisoryRAGChain initialised | Model: {model} | Top-K: {top_k}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        farmer_query: str,
        crop_hint: Optional[str] = None,
        language: Language = "auto",
        district: Optional[str] = None,
        use_weather: bool = True,
    ) -> RAGResponse:
        """
        Run the full RAG pipeline for a farmer's question.

        Args:
            farmer_query: The raw question from the farmer (any language).
            crop_hint: Optional explicit crop ('paddy' or 'wheat'). If None,
                       auto-detected from query text.
            language: Response language override. Default 'auto' detects from query.
            district: Optional Punjab district name (e.g. 'Ludhiana', 'Bathinda').
            use_weather: Whether to fetch live Open-Meteo weather & evaluate PAU gates.

        Returns:
            RAGResponse with the grounded answer, weather gates, and full metadata.
        """
        # 1. Detect crop & language
        detected_crop = crop_hint or _detect_crop(farmer_query)
        auto_lang = _detect_language(farmer_query)
        effective_lang = auto_lang if language == "auto" else language
        lang_instr = _language_instruction(language, auto_lang)

        # 2. Resolve weather & PAU weather gates
        weather_gate = None
        weather_context_text = None
        resolved_dist, _, _ = self.weather_service.resolve_district(district or farmer_query)

        if use_weather:
            weather_data = self.weather_service.get_weather(resolved_dist)
            if weather_data:
                weather_gate = self.weather_service.evaluate_gates(weather_data, crop=detected_crop)
                weather_context_text = weather_gate.weather_summary_text

        # 3. Retrieve relevant PAU chunks from ChromaDB
        raw_chunks = self.retriever.retrieve(
            query=farmer_query,
            crop_filter=detected_crop,
            top_k=self.top_k,
        )

        # 4. Confidence scoring — if all distances are high (poor match), fallback
        confidence = self._assess_confidence(raw_chunks)
        if confidence == "fallback":
            return self._build_fallback_response(
                farmer_query, detected_crop, effective_lang, raw_chunks
            )

        # 5. Build retrieved chunks list
        retrieved = [
            RetrievedChunk(
                id=c["id"],
                content=c["content"],
                metadata=c["metadata"],
                distance=c["distance"],
            )
            for c in raw_chunks
        ]

        # 6. Build the grounded prompt with PAU KB + Weather Gate context
        user_prompt = _build_user_prompt(
            farmer_query,
            raw_chunks,
            lang_instr,
            weather_context=weather_context_text,
        )

        # 7. Call Gemini
        raw_llm_text = self._call_gemini(user_prompt)

        # 8. Post-process: extract source IDs mentioned by LLM
        sources = self._extract_sources(raw_llm_text, retrieved)

        # 9. Append disclaimer
        answer_core = raw_llm_text.strip()
        answer = answer_core + SAFETY_DISCLAIMER if self.add_disclaimer else answer_core

        return RAGResponse(
            answer=answer,
            answer_core=answer_core,
            query=farmer_query,
            detected_crop=detected_crop,
            language_used=effective_lang,
            district=resolved_dist,
            weather_gate=weather_gate,
            retrieved_chunks=retrieved,
            sources=sources,
            confidence=confidence,
            raw_llm_output=raw_llm_text,
        )

    def query_stream(
        self,
        farmer_query: str,
        crop_hint: Optional[str] = None,
        language: Language = "auto",
        district: Optional[str] = None,
        use_weather: bool = True,
    ):
        """
        Streaming variant — yields text chunks as Gemini generates them.
        Useful for WhatsApp / real-time API responses.

        Yields:
            str chunks of the answer. The final chunk includes the disclaimer.
        """
        detected_crop = crop_hint or _detect_crop(farmer_query)
        auto_lang = _detect_language(farmer_query)
        lang_instr = _language_instruction(language, auto_lang)

        # Resolve live weather gate
        weather_context_text = None
        resolved_dist, _, _ = self.weather_service.resolve_district(district or farmer_query)
        if use_weather:
            weather_data = self.weather_service.get_weather(resolved_dist)
            if weather_data:
                gate = self.weather_service.evaluate_gates(weather_data, crop=detected_crop)
                weather_context_text = gate.weather_summary_text

        raw_chunks = self.retriever.retrieve(
            query=farmer_query,
            crop_filter=detected_crop,
            top_k=self.top_k,
        )

        confidence = self._assess_confidence(raw_chunks)
        if confidence == "fallback":
            yield KVK_FALLBACK_EN
            return

        user_prompt = _build_user_prompt(
            farmer_query,
            raw_chunks,
            lang_instr,
            weather_context=weather_context_text,
        )

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=self.temperature,
                max_output_tokens=1024,
            ),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

        if self.add_disclaimer:
            yield SAFETY_DISCLAIMER

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_gemini(self, user_prompt: str) -> str:
        """Send prompt to Gemini and return the text response."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=self.temperature,
                max_output_tokens=1024,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_ONLY_HIGH",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="BLOCK_ONLY_HIGH",
                    ),
                ],
            ),
        )
        return response.text or ""

    def _assess_confidence(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Assess retrieval quality from ChromaDB L2 distances.

        ChromaDB's DefaultEmbeddingFunction (ONNX all-MiniLM-L6-v2) is
        English-only. Empirical measurements on this PAU collection show:
          • Best-case Hinglish queries : L2 ≈ 1.2–1.5  → good enough
          • Punjabi/Hindi script queries: L2 ≈ 1.9–2.1  → embedder mismatch

        Thresholds are intentionally lenient to avoid false fallbacks while
        the collection still uses the English-only ONNX embedder.

        ⚠️  TODO (Phase 2 improvement): Re-embed the collection using
        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' to
        drastically improve Punjabi/Hindi retrieval accuracy.
        See: EMBEDDING_MODEL_NAME in config.py
        """
        if not chunks:
            return "fallback"

        distances = [c["distance"] for c in chunks]
        best = min(distances)

        # Empirically calibrated for ONNX MiniLM on this PAU collection
        if best < 1.3:
            return "high"
        elif best < 1.6:
            return "medium"
        elif best < 2.0:
            return "low"
        else:
            return "fallback"

    def _extract_sources(
        self,
        llm_text: str,
        retrieved: List[RetrievedChunk],
    ) -> List[str]:
        """
        Extract chunk IDs cited in the LLM response (from "📚 Source:" line),
        falling back to top retrieved chunk IDs if none are explicitly cited.
        """
        cited: List[str] = []
        for chunk in retrieved:
            if chunk.id in llm_text:
                cited.append(chunk.id)
        # Fallback: return IDs of top-2 retrieved chunks
        if not cited:
            cited = [c.id for c in retrieved[:2]]
        return cited

    def _build_fallback_response(
        self,
        query: str,
        detected_crop: Optional[str],
        language: str,
        chunks: List[Dict[str, Any]],
    ) -> RAGResponse:
        """Return a safe KVK-referral response when retrieval confidence is too low."""
        fallback_messages = {
            "punjabi": (
                "ਮੈਨੂੰ ਤੁਹਾਡੇ ਸਵਾਲ ਲਈ PAU ਦਿਸ਼ਾ-ਨਿਰਦੇਸ਼ਾਂ ਵਿੱਚ ਸਹੀ ਜਾਣਕਾਰੀ ਨਹੀਂ ਮਿਲੀ। "
                "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਨਜ਼ਦੀਕੀ ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ (KVK) ਨਾਲ ਸੰਪਰਕ ਕਰੋ।"
            ),
            "hindi": (
                "मुझे आपके प्रश्न के लिए PAU दिशा-निर्देशों में सटीक जानकारी नहीं मिली। "
                "कृपया अपने नज़दीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
            ),
            "english": KVK_FALLBACK_EN,
        }
        msg = fallback_messages.get(language, KVK_FALLBACK_EN)
        answer = msg + SAFETY_DISCLAIMER if self.add_disclaimer else msg

        return RAGResponse(
            answer=answer,
            answer_core=msg,
            query=query,
            detected_crop=detected_crop,
            language_used=language,
            retrieved_chunks=[],
            sources=[],
            confidence="fallback",
        )


# ---------------------------------------------------------------------------
# CLI smoke test — run directly: python src/rag_chain.py
# ---------------------------------------------------------------------------

def _print_response(resp: RAGResponse, index: int, total: int) -> None:
    """Pretty-print a RAGResponse to the terminal using Rich if available."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()
        console.print(f"\n[bold cyan]━━━ Query {index}/{total} ━━━[/bold cyan]")
        console.print(f"[yellow]Question:[/yellow] {resp.query}")
        console.print(
            f"[dim]Crop: {resp.detected_crop or 'unknown'} | "
            f"Lang: {resp.language_used} | "
            f"Confidence: {resp.confidence} | "
            f"Sources: {', '.join(resp.sources) or 'none'}[/dim]"
        )
        console.print(Panel(resp.answer, title="🌾 Kisan Mitra Response", border_style="green"))
    except ImportError:
        sep = "=" * 70
        print(f"\n{sep}")
        print(f"[{index}/{total}] Query: {resp.query}")
        print(f"Crop: {resp.detected_crop} | Lang: {resp.language_used} | Confidence: {resp.confidence}")
        print(f"Sources: {resp.sources}")
        print(f"\n--- ANSWER ---\n{resp.answer}")
        print(sep)


if __name__ == "__main__":
    # Representative multilingual test queries covering paddy & wheat
    TEST_QUERIES = [
        {
            "query": "PR 126 lagayi hai 25 din ho gaye, urea kab daalu aur kitna?",
            "description": "Paddy urea timing (Hinglish)",
        },
        {
            "query": "ਕਣਕ ਵਿੱਚ ਪੀਲੀ ਕੁੰਗੀ ਦੇ ਲੱਛਣ ਅਤੇ ਰੋਕਥਾਮ ਕਿਵੇਂ ਕਰੀਏ?",
            "description": "Wheat Yellow Rust (Punjabi)",
        },
        {
            "query": "Wheat crop me pehla paani CRI stage pe kab dena chahiye?",
            "description": "Wheat first irrigation (Hindi)",
        },
        {
            "query": "Should I stop irrigating paddy before harvesting?",
            "description": "Paddy pre-harvest cutoff (English)",
        },
        {
            "query": "ਝੋਨੇ ਵਿੱਚ DAP ਕਿੰਨੀ ਅਤੇ ਕਦੋਂ ਪਾਉਣੀ ਚਾਹੀਦੀ ਹੈ ਜੇਕਰ ਕਣਕ ਵਿੱਚ ਪਹਿਲਾਂ ਤੋਂ DAP ਪਾਈ ਹੋਈ ਹੈ?",
            "description": "Paddy DAP carryover (Punjabi)",
        },
    ]

    chain = CropAdvisoryRAGChain(temperature=0.15)

    for i, tc in enumerate(TEST_QUERIES, 1):
        print(f"\nRunning query {i}/{len(TEST_QUERIES)}: {tc['description']}")
        try:
            response = chain.query(tc["query"])
            _print_response(response, i, len(TEST_QUERIES))
        except Exception as exc:
            print(f"❌ ERROR on query {i}: {exc}")
