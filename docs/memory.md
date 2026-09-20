# Kisan Mitra — Project Memory

## Purpose

This document records important architectural and product decisions so future development sessions can quickly understand the project's current state.

## Current Product

**Name:** Kisan Mitra

**Description:** AI-powered crop advisory for farmers, initially focused on Punjab.

**Live Demo:** https://kisan-mitra-advis0ry.streamlit.app/

**Repository:** https://github.com/steeltroops11/Crop_Advisory

## Current Architecture

The deployed application is a single Streamlit application.

```text
Streamlit
   ↓
CropAdvisoryRAGChain
   ├── ChromaDB
   ├── Google Gemini
   └── Open-Meteo
```

There is no separate FastAPI service required for the current deployed demo.

## Important Repository Paths

```text
streamlit_app.py
src/config.py
src/embeddings.py
src/retriever.py
src/ingest.py
src/rag_chain.py
data/knowledge_base.json
requirements.txt
```

## Deployment Decisions

- Streamlit Community Cloud is the current deployment platform.
- `GEMINI_API_KEY` is supplied through Streamlit Secrets.
- `vector_db/` is ignored by Git because it is generated/runtime state.
- A missing Chroma collection triggers knowledge-base ingestion during startup.
- Open-Meteo is used without requiring a separate paid weather service.

## Current Supported Context

- Paddy
- Wheat
- English
- Hindi
- Punjabi
- Hinglish
- District context, including Ludhiana
- Weather-aware advisory

## Trust and Safety Decisions

- Responses should remain grounded in retrieved agricultural knowledge.
- The system should not fabricate missing agricultural information.
- Advisories contain an AI/KVK disclaimer.
- Critical chemical/agricultural decisions should be verified locally.

## Known Tradeoffs

The lightweight Chroma default embedding configuration reduces deployment complexity and dependency overhead. It may provide weaker multilingual semantic retrieval than a dedicated multilingual embedding model.

This is an accepted prototype tradeoff unless retrieval quality becomes a blocking issue.

## Do Not Reintroduce Without a Reason

- Separate backend deployment for the Streamlit demo
- Render-based deployment
- Hard-coded API keys
- Committed runtime vector database
- Unsupported agricultural claims
- Architecture documentation describing an older deployment as the current system

## Future Direction

The long-term product can evolve toward a personalized, multimodal agricultural assistant with:

- more crops
- farm profiles
- image analysis
- voice interaction
- expert feedback
- richer weather and crop-calendar intelligence
- stronger evaluation and observability
