import json
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import (
    KNOWLEDGE_BASE_PATH,
    VECTOR_DB_DIR,
    EMBEDDING_MODEL_NAME,
    CHROMA_COLLECTION_NAME,
)

def format_document_content(item: dict) -> str:
    """Format structured JSON into a semantically dense string for vector embedding."""
    varieties = ", ".join(item.get("variety", []))
    keywords = ", ".join(item.get("keywords", []))
    
    content = f"""CROP: {item.get('crop', '').upper()}
VARIETY: {varieties}
STAGE: {item.get('growth_stage', '')}
CATEGORY: {item.get('category', '').replace('_', ' ').upper()}
TOPIC: {item.get('title', '')}

RECOMMENDATION RULE:
{item.get('rule', '')}

ACTIONABLE GUIDANCE:
{item.get('actionable_guidance', '')}

AGRONOMIC REASONING:
{item.get('reasoning', '')}

CONDITIONS & APPLICABILITY:
{item.get('conditions', '')}

SEARCH KEYWORDS & LOCAL TERMS:
{keywords}

SOURCE: {item.get('source', '')}
"""
    return content.strip()

def ingest_knowledge_base():
    """Ingest structured knowledge base into persistent ChromaDB."""
    print(f"Loading knowledge base from: {KNOWLEDGE_BASE_PATH}")
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        raise FileNotFoundError(f"Knowledge base not found at {KNOWLEDGE_BASE_PATH}")

    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} agronomic knowledge entries.")

    # Initialize ChromaDB client
    import chromadb
    from src.embeddings import get_embedding_function

    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

    # Use the same embedding backend for both ingestion and retrieval.
    print(f"Initializing embedding function: {EMBEDDING_MODEL_NAME}...")
    embed_fn = get_embedding_function()

    # Recreate or get collection
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"description": "PAU Crop Advisory Knowledge Base for Punjab"},
    )

    documents = []
    metadatas = []
    ids = []

    for item in data:
        doc_text = format_document_content(item)
        documents.append(doc_text)
        ids.append(item["id"])
        
        # Flatten metadata for Chroma compatibility
        metadatas.append({
            "crop": str(item.get("crop", "")),
            "category": str(item.get("category", "")),
            "growth_stage": str(item.get("growth_stage", "")),
            "title": str(item.get("title", "")),
            "source": str(item.get("source", "")),
        })

    print(f"Indexing {len(documents)} documents into ChromaDB collection '{CHROMA_COLLECTION_NAME}'...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"Successfully indexed {collection.count()} chunks into {VECTOR_DB_DIR}!")
    return collection

if __name__ == "__main__":
    ingest_knowledge_base()
