# 🌾 AI Crop Advisory for Small Farmers — Beginner's Learning Roadmap

> This guide translates the project plan into **what you need to learn and do**, step by step, even if you're starting from scratch.

---

## 📌 What Is This Project?

You're building an **AI-powered WhatsApp chatbot** that helps small farmers (like those in Punjab) get advice on:
- 💧 When to irrigate their crops
- 🌱 How much fertilizer to use and when
- 🐛 Pest/disease alerts
- 🌾 Best sowing windows

It uses a technique called **RAG (Retrieval-Augmented Generation)** — the AI fetches real agricultural documents and answers based on them, so it doesn't make things up.

---

## 🗺️ The Full Roadmap (Simplified)

| Phase | What You're Doing | Duration |
|-------|-------------------|----------|
| **Phase 0** | Talk to farmers / understand the problem | 1–2 weeks |
| **Phase 1** | Build a knowledge base from PAU bulletins | 2–3 weeks |
| **Phase 2** | Build the RAG pipeline (AI core) | 2–3 weeks |
| **Phase 3** | Add language support + WhatsApp | 2 weeks |
| **Phase 4** | Backend API (FastAPI) | 1–2 weeks |
| **Phase 5** | Demo dashboard (Streamlit / React) | 1 week |
| **Phase 6** | Testing & Safety guardrails | 1 week |
| **Phase 7** | Deploy it online | 1 week |
| **Phase 8** | Collect feedback, improve | Ongoing |

**Total: ~10–12 weeks** working part-time

---

## 🧠 What You Need to Learn (In Order)

### 🟢 Step 1 — Python Basics (if not already done)
> Everything in this project runs on Python.

**Learn:**
- Variables, loops, functions, classes
- File reading/writing (especially PDFs and JSON)
- Working with APIs (requests library)

**Free Resources:**
- [Python for Everybody – Coursera](https://www.coursera.org/specializations/python) (free to audit)
- [freeCodeCamp Python](https://www.youtube.com/watch?v=rfscVS0vtbw)

**Time:** 1–2 weeks if you're new

---

### 🟡 Step 2 — Understand RAG (The Core Concept)
RAG = **Retrieve** relevant documents → **Augment** the prompt → **Generate** the answer

Think of it like this:
```
Farmer asks: "When should I water my paddy?"
     ↓
System searches the PAU irrigation bulletin
     ↓
Finds: "Paddy in tillering stage needs 5cm standing water every 5 days"
     ↓
AI replies in Punjabi/Hindi using that fact
```

**Learn:**
- What are embeddings? (converting text into numbers so AI can search it)
- What is a vector database? (stores those numbers for fast search)
- How LLMs work at a high level

**Free Resources:**
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [IBM What is RAG?](https://research.ibm.com/blog/retrieval-augmented-generation-RAG) (plain English)
- YouTube: search "RAG tutorial beginner Python 2024"

**Time:** 3–5 days to understand the concept

---

### 🟡 Step 3 — Tools & Libraries to Learn

| Tool | What It Does | Where to Learn |
|------|-------------|----------------|
| **LangChain** | Connects LLM + retrieval together | [LangChain Docs](https://python.langchain.com) |
| **Chroma / Qdrant** | Vector database (stores embeddings) | [Chroma Quickstart](https://docs.trychroma.com/getting-started) |
| **FastAPI** | Build the backend API | [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) |
| **Streamlit** | Quick dashboard/demo UI | [Streamlit Docs](https://docs.streamlit.io) |
| **OpenAI / Gemini API** | The LLM brain | Sign up + read docs |
| **Twilio / Meta WhatsApp API** | Send/receive WhatsApp messages | [Twilio Sandbox](https://www.twilio.com/docs/whatsapp) |

---

### 🔵 Step 4 — Build Phase 0 First (Before Any Code!)
> **This is the most important phase** — your PDF says so too.

**What to do:**
1. Talk to 3–5 farmers (or agri students, or a KVK extension worker)
2. Ask them: *"When you need to decide irrigation or fertilizer, who do you currently ask?"*
3. Note down the **exact words** they use — this becomes your test data

**Why?** Because you need to know **what real farmers actually ask**, not what you think they ask. A question like *"dhan vich pani kado dena hai?"* (When to water paddy?) is very different from a textbook query.

**KVK = Krishi Vigyan Kendra** — Government agriculture advisory centers in every district. You can visit or email them.

---

## 🏗️ How to Build It — Phase by Phase

### Phase 1: Knowledge Base
**Goal:** Collect official agriculture documents and structure them properly.

**What to do:**
1. Download PAU (Punjab Agricultural University) crop bulletins (PDFs available on their website)
2. Also look for ICAR crop guides
3. Parse these PDFs with Python (`pdfplumber` or `PyMuPDF` library)
4. Structure the data like this:

```json
{
  "crop": "paddy",
  "stage": "tillering",
  "condition": "no rain in 5 days",
  "action": "irrigate with 5cm standing water",
  "source": "PAU Bulletin 2024"
}
```

**Don't** just dump raw PDFs into the system — that's the mistake most beginners make.

---

### Phase 2: RAG Pipeline
**Goal:** Build the AI that searches your knowledge base and answers questions.

**Simple starting architecture:**
```
[Farmer Query] → [Query Understanding] → [Hybrid Search] → [LLM] → [Answer]
```

**Step-by-step:**
1. **Embed your documents** using `bge-m3` or `multilingual-e5` (multilingual models that understand Punjabi/Hindi)
2. **Store embeddings** in Chroma (easy to start) or Qdrant
3. **Add keyword search** (BM25) alongside vector search — crop names and pest names need exact matches
4. **Connect to LLM** (Gemini API is free/cheap, or use OpenAI)
5. **Strict grounding prompt** — tell the AI: *"Only answer from the provided context. If unsure, say 'consult your local KVK'"*

**Starter code to understand:**
```python
# Very simplified RAG flow
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# 1. Load your documents
# 2. Embed them
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vectorstore = Chroma.from_documents(docs, embeddings)

# 3. Search
results = vectorstore.similarity_search("paddy irrigation timing", k=3)

# 4. Send to LLM with results as context
```

---

### Phase 3: Language & WhatsApp
**Goal:** Make it work in Punjabi/Hindi via WhatsApp.

**Language:** Use a multilingual LLM (Gemini, GPT-4o) — they understand Hindi/Punjabi natively. No need for separate translation.

**WhatsApp setup:**
1. Sign up for Twilio free trial
2. Connect Twilio WhatsApp Sandbox to your bot
3. When a farmer texts → Twilio webhook → your FastAPI server → RAG pipeline → reply

**Voice input (bonus):** Use OpenAI Whisper to convert voice messages to text first.

---

### Phase 4: Backend API (FastAPI)
**Goal:** Create a server that receives WhatsApp messages and responds.

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/whatsapp")
async def receive_message(Body: str, From: str):
    # 1. Parse the incoming message
    # 2. Run through RAG pipeline
    # 3. Return the answer
    answer = rag_pipeline(Body)
    return {"response": answer}
```

---

### Phase 5: Demo Dashboard (Streamlit)
**Goal:** A simple web UI to show your project to others.

```python
import streamlit as st
st.title("AI Crop Advisory Demo")
query = st.text_input("Ask a farming question:")
if query:
    answer = rag_pipeline(query)
    st.write(answer)
```

That's literally all you need for a basic demo!

---

## ⚠️ Critical Safety Rules
> **Wrong farming advice can cause real crop loss and financial damage to farmers.**

1. **Always add disclaimer:** *"This is AI-generated advice. Consult your local KVK for critical decisions."*
2. **Build a fallback:** If the AI isn't confident → don't guess → say *"I don't have enough information, please consult KVK"*
3. **Never hallucinate:** The system prompt must strictly enforce: only answer from retrieved documents

---

## 🛠️ Tech Stack Summary

```
┌─────────────────────────────────────────────────┐
│                  FARMER (WhatsApp)               │
└────────────────────┬────────────────────────────┘
                     │ WhatsApp message
                     ▼
┌─────────────────────────────────────────────────┐
│              Twilio / Meta API                  │
└────────────────────┬────────────────────────────┘
                     │ webhook
                     ▼
┌─────────────────────────────────────────────────┐
│           FastAPI Backend (Python)              │
│  ┌──────────────────────────────────────────┐  │
│  │         RAG Pipeline                     │  │
│  │  Query → Embed → Search → LLM → Answer  │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Vector Store │  │  Structured KB (Postgres)│ │
│  │ (Chroma/     │  │  + Weather API (Open-    │ │
│  │  Qdrant)     │  │  Meteo / IMD)            │ │
│  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 📚 Your Learning Path (Week by Week)

| Week | Focus |
|------|-------|
| **Week 1** | Revise Python basics, learn what RAG is, watch 2–3 YouTube tutorials |
| **Week 2** | Phase 0 — Talk to farmers/KVK, download PAU documents |
| **Week 3** | Learn LangChain basics, build a simple RAG with a local PDF |
| **Week 4** | Build Phase 1 — Parse and structure agri documents properly |
| **Week 5** | Build Phase 2 — Full RAG pipeline with multilingual embeddings |
| **Week 6** | Add weather API, test with real farmer-style questions |
| **Week 7** | Phase 3 — Set up Twilio WhatsApp sandbox, connect to your backend |
| **Week 8** | Phase 4+5 — FastAPI server + Streamlit demo dashboard |
| **Week 9** | Phase 6 — Testing, safety guardrails, edge cases |
| **Week 10** | Phase 7 — Deploy on Railway/Render |
| **Week 11–12** | Real pilot with 5–10 users, fix what breaks |

---

## 🚀 Where to Start RIGHT NOW (Today)

1. **Install Python** (if not done): [python.org](https://python.org)
2. **Get a free API key:** [Google AI Studio](https://aistudio.google.com) (Gemini is free)
3. **Run this in 10 minutes** to see RAG work:
   ```bash
   pip install langchain chromadb langchain-community sentence-transformers
   ```
4. **Download one PAU PDF** from [pau.edu/crop-advisory](https://pau.edu) as your first knowledge base
5. **Follow this YouTube tutorial** to build your first RAG: search *"LangChain RAG PDF Python tutorial"*

---

## 💡 Remember

> **Your PDF says it best:** *"The unlock here is — doing the real pilot first doesn't cost you portfolio quality — it's what generates the portfolio quality."*
>
> Start narrow: **one crop (paddy), one district (Ludhiana), three farmers** — then expand.
> A real WhatsApp screenshot from an actual farmer is worth more than any polished demo UI.

---

*Generated based on: AI Crop Advisory for Small Farmers.pdf*
