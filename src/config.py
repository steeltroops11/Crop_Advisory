import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base.json"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Multilingual embedding model for English, Hindi, and Punjabi
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
CHROMA_COLLECTION_NAME = "pau_crop_advisory"

# Weather API settings (Open-Meteo)
OPEN_METEO_BASE_URL = os.getenv(
    "OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast"
)
DEFAULT_DISTRICT = "Ludhiana"
DEFAULT_LATITUDE = 30.9010
DEFAULT_LONGITUDE = 75.8573

