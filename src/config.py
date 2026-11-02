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
