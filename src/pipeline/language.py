import re
from typing import Dict, Any

# Common phonetic romanized Hindi/Hinglish vocabulary tokens in Indian investing conversations
HINGLISH_WORDS = {
    "kya", "kyu", "kyun", "nahi", "nhi", "hai", "hain", "karna", "krna", "paisa",
    "paise", "rupaye", "mujhe", "mera", "meri", "hum", "kaise", "hota", "hoti",
    "ruk", "rok", "band", "shuru", "kharab", "achha", "accha", "thik", "theek",
    "bhai", "kat", "kata", "gaya", "gye", "gya", "aaraha", "aaya", "aayi", "chal",
    "raha", "rahe", "rahi", "sahi", "galat", "matlab", "kitna", "kab", "kuch",
    "batao", "bataiye", "badha", "kam", "ghat", "lagaya", "daala", "nuksan",
    "faida", "wapas", "nikal", "daal", "pehle", "baad", "abhi", "karte", "karu",
    "kare", "sakta", "sakti", "gayi", "mil", "mila", "milega", "dekh", "dekha"
}

# Regex to detect Devanagari script (Hindi, Marathi, etc.)
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

def detect_language(text: str) -> str:
    """
    Detects whether text is in English ('en'), Hindi ('hi'), or Hinglish ('hinglish').
    - Devanagari characters -> 'hi'
    - Roman script with significant density of Hinglish markers -> 'hinglish'
    - Default -> 'en'
    """
    if not text or not text.strip():
        return "en"

    # Check for Devanagari script
    devanagari_chars = len(DEVANAGARI_REGEX.findall(text))
    total_letters = len(re.findall(r"\w", text))
    
    if total_letters > 0 and (devanagari_chars / total_letters) > 0.15:
        return "hi"

    # Tokenize words into lower-case alphanumeric tokens
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
    if not words:
        return "en"

    hinglish_count = sum(1 for w in words if w in HINGLISH_WORDS)
    ratio = hinglish_count / len(words)

    # If at least 2 Hinglish words and ratio >= 0.08, or 3+ Hinglish words
    if (hinglish_count >= 2 and ratio >= 0.08) or hinglish_count >= 3:
        return "hinglish"

    return "en"

def normalize_hinglish_terms(text: str) -> str:
    """
    Normalizes common Hinglish colloquial abbreviations and typos to standard terms.
    Preserves original sentence flow while aiding downstream search and embeddings.
    """
    replacements = {
        r"\bnhi\b": "nahi",
        r"\bkrna\b": "karna",
        r"\bkr\b": "kar",
        r"\bplz\b": "please",
        r"\bpls\b": "please",
        r"\bmf\b": "mutual fund",
        r"\bmfs\b": "mutual funds",
        r"\bretuns\b": "returns",
        r"\breturnz\b": "returns",
        r"\bwidraw\b": "withdraw",
        r"\bacc\b": "account",
    }
    normalized = text
    for pattern, repl in replacements.items():
        normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
    return normalized

