import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# PROJECT DIRECTORIES & CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv()


UPLOAD_DIR = BASE_DIR / "static" / "uploads"

MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "leaf_care_mobilenetv2.keras"

LABELS_PATH = MODEL_DIR / "class_names.json"


# ============================================================
# IMAGE SETTINGS
# ============================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png"
}

MAX_UPLOAD_MB = int(
    os.getenv(
        "MAX_UPLOAD_MB",
        "5"
    )
)

IMAGE_SIZE = (
    224,
    224
)


# ============================================================
# MODEL SETTINGS
# ============================================================

TOP_K = 3


# ============================================================
# GENERATIVE AI SETTINGS
# ============================================================

"""
Available providers:

none
    Uses the built-in knowledge base.

ollama
    Uses a local/open LLM through Ollama.

gemini
    Uses Google Gemini API.
"""

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "none"
).lower()


# ============================================================
# OLLAMA SETTINGS
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)


# ============================================================
# GOOGLE GEMINI SETTINGS
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest"
)


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

CLASSES_PATH = LABELS_PATH

OLLAMA_API_URL = f"{OLLAMA_URL.rstrip('/')}/api/generate"

MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
