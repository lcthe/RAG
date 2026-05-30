"""Backend configuration via environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # web_app/
DATA_DIR = ROOT.parent / "data"
LOG_DIR = ROOT / "data" / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Vector Database - Chroma (no Docker needed)
CHROMA_PERSIST_DIR = str(ROOT / "data" / "chroma_db")
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Redis - use existing container on port 6379
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

# LLM API
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Embedding
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local_bge")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "512"))

# RAG defaults
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
DEFAULT_TOP_K = int(os.getenv("TOP_K", "5"))

# Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "18762"))
