"""Shared ChromaDB embedding function factory.

Keeps ingestion and retrieval on the same embedding backend. If the optional
sentence-transformers dependency is unavailable, the project falls back to
Chroma's default local embedding function so demos and tests still run.
"""

from chromadb.utils import embedding_functions

from src.config import EMBEDDING_MODEL_NAME


def get_embedding_function():
    """Return the configured Chroma embedding function with a safe fallback."""
    if EMBEDDING_MODEL_NAME.lower() in {"default", "chroma-default", "onnx-default"}:
        return embedding_functions.DefaultEmbeddingFunction()

    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
    except Exception as exc:
        print(
            "⚠️ Could not initialize sentence-transformer embedding "
            f"'{EMBEDDING_MODEL_NAME}': {exc}"
        )
        print("↳ Falling back to Chroma DefaultEmbeddingFunction for local demo.")
        return embedding_functions.DefaultEmbeddingFunction()
