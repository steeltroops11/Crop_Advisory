import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import VECTOR_DB_DIR, CHROMA_COLLECTION_NAME
from src.embeddings import get_embedding_function

class CropKnowledgeRetriever:
    def __init__(self):
        import chromadb

        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.embed_fn = get_embedding_function()

        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embed_fn,
        )

    def retrieve(
        self,
        query: str,
        crop_filter: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant PAU guidelines with optional crop metadata filtering."""
        where_clause = None
        if crop_filter and crop_filter.lower() in ["paddy", "wheat"]:
            where_clause = {"crop": crop_filter.lower()}

        expanded_query = self._expand_local_terms(query)

        results = self.collection.query(
            query_texts=[expanded_query],
            n_results=top_k,
            where=where_clause,
        )

        formatted_results = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
                formatted_results.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                })

        return formatted_results

    def _expand_local_terms(self, query: str) -> str:
        """Add English agronomy keywords for common Punjabi/Hinglish terms."""
        q = query.lower()
        expansions = []

        if "ਪੀਲੀ ਕੁੰਗੀ" in query or "peeli kungi" in q or "yellow rust" in q:
            expansions.append(
                "yellow rust peeli kungi wheat disease bright yellow powdery stripes "
                "propiconazole tilt 25 ec nativo pustules"
            )

        if "ਪਹਿਲਾ ਪਾਣੀ" in query or "pehla paani" in q or "first irrigation" in q:
            expansions.append("first irrigation wheat crown root initiation CRI 20 25 DAS")

        if "ਯੂਰੀਆ" in query or "urea" in q:
            expansions.append("urea nitrogen fertilizer dose timing")

        if "ਡੀਏਪੀ" in query or "dap" in q:
            expansions.append("DAP phosphorus fertilizer basal dose")

        return " ".join([query, *expansions])

if __name__ == "__main__":
    retriever = CropKnowledgeRetriever()
    test_queries = [
        "dhan me urea kab aur kitna dalna hai PR 126 me?",
        "wheat first irrigation timing CRI stage",
        "peele patte yellow rust treatment in wheat",
    ]
    for q in test_queries:
        print(f"\n================ QUERY: {q} ================")
        res = retriever.retrieve(q, top_k=1)
        for r in res:
            print(f"Match [{r['id']}] (Distance: {r['distance']:.4f}):")
            print(r['content'][:300] + "...\n")
