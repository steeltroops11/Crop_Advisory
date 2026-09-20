# Kisan Mitra — System Architecture

## 1. Architecture Overview

Kisan Mitra follows a lightweight cloud-deployed RAG architecture:

```text
                         ┌──────────────────────┐
                         │      Farmer/User     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Streamlit Web UI   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌────────────────────────────┐
                     │   CropAdvisoryRAGChain     │
                     │  Query + Context Control   │
                     └───────┬───────────┬────────┘
                             │           │
                    ┌────────▼──────┐   ┌▼──────────────┐
                    │   ChromaDB    │   │  Open-Meteo   │
                    │ Vector Search │   │ Weather Data  │
                    └────────┬──────┘   └──────┬────────┘
                             │                 │
                             └────────┬────────┘
                                      ▼
                              ┌───────────────┐
                              │ Google Gemini │
                              │ LLM Generation│
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ Final Advisory│
                              │ + Source      │
                              │ + Safety Note │
                              └───────────────┘
```

## 2. Major Components

### Streamlit Application

`streamlit_app.py` is the deployment entry point. It provides the user interface and directly invokes the RAG chain.

### RAG Chain

`src/rag_chain.py` coordinates:

- query interpretation
- crop detection
- language handling
- weather retrieval
- knowledge retrieval
- confidence assessment
- grounded prompt construction
- Gemini generation

### Retriever

`src/retriever.py` manages ChromaDB retrieval.

If the collection is absent in a fresh cloud environment, the retriever invokes the knowledge-base ingestion process before continuing.

### Ingestion

`src/ingest.py` loads the structured knowledge base from:

```text
data/knowledge_base.json
```

and builds the ChromaDB collection.

### Embeddings

`src/embeddings.py` provides the embedding function used by ChromaDB.

The deployment can use ChromaDB's default embedding backend to keep the cloud dependency footprint lightweight.

### Weather Service

The weather component communicates with Open-Meteo and provides weather context used by weather-sensitive advisory logic.

### Configuration

`src/config.py` centralizes:

- API secrets
- vector database location
- collection name
- knowledge-base location
- default district/location
- Open-Meteo configuration

## 3. Data Flow

```text
User Query
   ↓
Normalize / Detect Context
   ↓
Expand Local Agronomy Terms
   ↓
Semantic Retrieval
   ↓
Top-K Knowledge Chunks
   ↓
Optional Weather Context
   ↓
Grounded Gemini Prompt
   ↓
Generated Advisory
   ↓
Source + Safety Disclaimer
```

## 4. Deployment Architecture

```text
GitHub Repository
       │
       ▼
Streamlit Community Cloud
       │
       ▼
streamlit_app.py
       │
       ├── RAG Chain
       ├── ChromaDB
       ├── Gemini
       └── Open-Meteo
```

The vector database is intentionally not committed to Git because `vector_db/` is ignored. On a fresh deployment, the application can build the required collection from the version-controlled knowledge base.

## 5. Security Boundaries

Secrets such as `GEMINI_API_KEY` are supplied through Streamlit Secrets and are not stored in source control.

The application should never expose API credentials in UI output, logs, screenshots, documentation, or Git history.

## 6. Architectural Principles

- Retrieval before generation
- Domain grounding over generic generation
- Explicit uncertainty
- Minimal external dependencies
- Stateless web deployment where possible
- Secrets outside source control
- Modular separation of configuration, retrieval, generation, and UI
