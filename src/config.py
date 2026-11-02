import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

DATA_DIR.mkdir(exist_ok=True)
RAW_DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DATA_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "app.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Privacy & Security
HASH_SALT = os.getenv("HASH_SALT", "groww_sip_discovery_salt_2026")

def resolve_groq_model(client=None) -> str:
    """
    Resolves the best available Groq model for the authenticated client account.
    Prioritizes explicit GROQ_MODEL in env if valid in account, otherwise auto-discovers.
    """
    candidate_priority = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "mixtral-8x7b-32768"
    ]
    env_model = os.getenv("GROQ_MODEL")
    if client:
        try:
            available = {m.id for m in client.models.list().data}
            if env_model and env_model in available:
                return env_model
            for candidate in candidate_priority:
                if candidate in available:
                    return candidate
            if available:
                chat_candidates = [m for m in available if "guard" not in m and "whisper" not in m]
                if chat_candidates:
                    return chat_candidates[0]
        except Exception:
            pass
    return env_model or "openai/gpt-oss-120b"

# Target Apps Configuration for Play Store & App Store
# Format: key -> {name, play_store_id, app_store_id}
MONITORED_APPS = {
    "groww": {
        "name": "Groww",
        "play_store_id": "com.nextbillion.groww",
        "app_store_id": "1404871703",  # Groww: Stocks & Mutual Fund
    },
    "zerodha_coin": {
        "name": "Zerodha Coin",
        "play_store_id": "com.zerodha.coin",
        "app_store_id": "1392892554",  # Coin by Zerodha
    },
    "indmoney": {
        "name": "INDmoney",
        "play_store_id": "in.indwealth",
        "app_store_id": "1450712684",  # INDmoney
    },
    "kuvera": {
        "name": "Kuvera",
        "play_store_id": "com.gooogle.android.kuvera.app",
        "app_store_id": "1329700901",  # Kuvera
    },
    "et_money": {
        "name": "ET Money",
        "play_store_id": "com.smartspends",
        "app_store_id": "1089078696",  # ET Money
    },
    "paytm_money": {
        "name": "Paytm Money",
        "play_store_id": "com.paytmmoney",
        "app_store_id": "1344917520",  # Paytm Money
    },
}
