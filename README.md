# Kisan Mitra — AI Crop Advisory for Small Farmers

Kisan Mitra is a PAU-grounded crop advisory assistant for small farmers in Punjab. It uses a Retrieval-Augmented Generation (RAG) pipeline over Punjab Agricultural University style crop recommendations, district-level weather gates, and multilingual responses for Hindi, Punjabi, English, and Hinglish queries.

## Core Features

- **RAG over PAU crop knowledge**: structured paddy and wheat recommendations stored in ChromaDB.
- **Multilingual farmer interface**: supports Hindi, Punjabi/Gurmukhi, English, and Hinglish.
- **Weather-aware advisory**: irrigation and fertilizer recommendations are gated by district weather conditions.
- **Safety-by-design**: every advisory includes AI/KVK disclaimers and avoids unsupported crop advice.
- **API-first backend**: FastAPI JSON endpoints for dashboard/mobile clients.
- **WhatsApp-ready architecture**: Twilio-compatible webhook route is implemented; free local simulation is available for demonstration.
- **LLM evaluation suite**: Gemini-as-judge evals for faithfulness, relevance, language, safety, and agronomic accuracy.

## Project Structure

```text
src/
  api.py              FastAPI backend and Twilio-compatible webhook
  rag_chain.py        RAG orchestration with Gemini
  retriever.py        ChromaDB retrieval
  ingest.py           Knowledge-base ingestion into ChromaDB
  embeddings.py       Shared embedding backend with free local fallback
  weather.py          Open-Meteo weather gate logic
  session_manager.py  Multi-turn WhatsApp/session memory

data/
  knowledge_base.json Structured PAU-style crop knowledge

tests/
  eval_llm.py         LLM evaluation suite
  test_api.py         API and webhook tests
  test_rag_chain.py   RAG behavior tests

scripts/
  simulate_whatsapp.py Free local Twilio webhook simulator
```

## Setup

```bash
cd /home/navish/Crop_advisory
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `GEMINI_API_KEY` in `.env`. For the free local demo, keep:

```env
EMBEDDING_MODEL_NAME=default
```

Then build the vector database:

```bash
python src/ingest.py
```

## Run the Backend

```bash
source .venv/bin/activate
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Open the interactive API docs:

```text
http://localhost:8000/docs
```

Use `POST /api/v1/advisory` with a query such as:

```json
{
  "query": "PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?",
  "crop": "paddy",
  "district": "Ludhiana",
  "language": "auto",
  "use_weather": true
}
```

## Free WhatsApp Webhook Demo

Twilio paid setup is **not required** for the submission demo. The implemented webhook can be tested locally with:

```bash
source .venv/bin/activate
python scripts/simulate_whatsapp.py "Wheat crop me pehla paani kab lagayein?"
```

This sends the same form payload that Twilio sends to `/webhook/whatsapp` and prints the TwiML XML response.

## Evaluation

Run the full LLM evaluation suite:

```bash
source .venv/bin/activate
python tests/eval_llm.py
```

Target: average score **≥ 4.0 / 5.0**.

The eval suite measures:

1. **Faithfulness** — grounded in retrieved PAU context.
2. **Answer relevance** — directly addresses the farmer question.
3. **Language compliance** — correct language/script.
4. **Safety compliance** — KVK referral and AI disclaimer.
5. **Agronomic accuracy** — correct crop timings, doses, and warnings.

Reports are saved under `tests/eval_reports/`.

## Docker Deployment

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8000/docs
```

## Submission Positioning

For the Sept 21 submission, present Twilio as **production-ready integration architecture** and use the FastAPI docs plus `scripts/simulate_whatsapp.py` as the free demo path. The most important evaluated work is the PAU-grounded RAG advisory engine, vector database, safety controls, weather gates, and eval report.
