# Kisan Mitra Submission Checklist

## Status

| Area | Status | Evidence |
|---|---:|---|
| PAU knowledge base | Ready | `data/knowledge_base.json` with paddy and wheat entries |
| Vector database | Ready | `vector_db/` rebuilt from 26 entries via `python src/ingest.py` |
| RAG chain | Ready | `src/rag_chain.py` retrieves PAU chunks and calls Gemini |
| Weather gates | Ready | `src/weather.py` integrates Open-Meteo district advisories |
| API backend | Ready | `src/api.py`, `GET /health`, `POST /api/v1/advisory`, `POST /api/v1/weather` |
| WhatsApp architecture | Ready without paid live Twilio | `POST /webhook/whatsapp` and `scripts/simulate_whatsapp.py` |
| Safety controls | Ready | KVK/AI disclaimer appended to advisory responses |
| Evaluation suite | Ready | `tests/eval_llm.py` with five weighted quality criteria |
| Docker deployment | Ready | `Dockerfile` and `docker-compose.yml` added |
| Local free demo | Ready | FastAPI Swagger UI and webhook simulator |

## What to Submit / Show

1. **Problem statement**
   - Small farmers in Punjab need timely, crop-stage-specific, local-language guidance.
   - Advice must be trustworthy, low-cost, and grounded in agricultural best practices.

2. **Solution overview**
   - Kisan Mitra is an AI crop advisory assistant using RAG over PAU-style crop knowledge.
   - It supports paddy and wheat queries, multilingual answers, weather-aware gates, and KVK safety disclaimers.

3. **Target users**
   - Small and marginal farmers in Punjab.
   - Extension workers, KVK advisors, and agri-support teams.

4. **Responsible AI**
   - Uses retrieved PAU context instead of free-form hallucination.
   - Includes KVK referral and AI-generated disclaimer.
   - Falls back to KVK guidance for unsupported/out-of-scope questions.
   - Avoids relying on paid Twilio for demo; webhook is simulated locally.

5. **Expected impact**
   - Faster advisory access for farmers.
   - Better fertilizer and irrigation timing.
   - Reduced crop risk from wrong timing and weather-insensitive decisions.
   - Local-language accessibility.

6. **Prototype/demo evidence**
   - Run backend: `uvicorn src.api:app --host 0.0.0.0 --port 8000`.
   - Open: `http://localhost:8000/docs`.
   - Demo `POST /api/v1/advisory` with real farmer queries.
   - Demo WhatsApp route for free: `python scripts/simulate_whatsapp.py "PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?"`.

7. **Evaluation evidence**
   - Run: `python tests/eval_llm.py`.
   - Include the average score and pass count in slides/report.
   - Mention criteria: Faithfulness 30%, Relevance 25%, Safety 20%, Agronomic Accuracy 15%, Language 10%.

## Demo Queries

### Paddy fertilizer
```text
PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?
```

### Wheat irrigation
```text
Gehun me pehla paani kab lagana chahiye?
```

### Punjabi disease query
```text
ਕਣਕ ਵਿੱਚ ਪੀਲੀ ਕੁੰਗੀ ਦੇ ਲੱਛਣ ਦੱਸੋ ਅਤੇ ਰੋਕਥਾਮ ਕਿਵੇਂ ਕਰੀਏ?
```

### Weather-gated paddy irrigation
```text
Ludhiana me aaj paddy me paani lagana hai?
```

## Important Twilio Note for Submission

Do **not** claim that paid Twilio live WhatsApp is active if you cannot pay/activate it. Say:

> The system includes a Twilio-compatible WhatsApp webhook and multi-turn session memory. Since live Twilio sandbox activation may require account billing, the submission demonstrates this integration using a free local webhook simulator that sends the same payload format and verifies the same backend route.

This is honest and technically strong.
