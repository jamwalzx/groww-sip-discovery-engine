import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz

from src.pipeline.language import detect_language, normalize_hinglish_terms

logger = logging.getLogger("pipeline.cleaner")

# Regex heuristics for promotional spam, referral links, WhatsApp groups, and bot dumps
SPAM_PATTERNS = [
    (re.compile(r"(use\s+my\s+referral|referral\s+code|invite\s+code|bonus\s+code|coupon\s+code)", re.I), "referral_code"),
    (re.compile(r"(t\.me\/|telegram\.me\/|join\s+my\s+telegram|join\s+telegram|telegram\s+channel)", re.I), "telegram_promotion"),
    (re.compile(r"(chat\.whatsapp\.com\/|join\s+whatsapp\s+group|whatsapp\s+me\s+at|dm\s+for\s+tips)", re.I), "whatsapp_group_spam"),
    (re.compile(r"(guaranteed\s+returns|100%\s+profit|daily\s+profit\s+tips|call\s+me\s+on\s+\+?91\s*[0-9]{10})", re.I), "financial_scam_tips"),
    (re.compile(r"(crypto\s+pump|binance\s+airdrop|free\s+crypto|earn\s+\$?[0-9]+\s*per\s+day)", re.I), "crypto_spam"),
]

def normalize_text_for_dedupe(text: str) -> str:
    """
    Strips punctuation, excessive whitespace, and lowercases text for deduplication matching.
    """
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

class DataCleaner:
    """
    Deduplicates, identifies spam/promotions, detects language (English, Hindi, Hinglish),
    and normalizes text while preserving exact verbatim text for quote integrity.
    """

    def __init__(self, similarity_threshold: float = 90.0):
        self.similarity_threshold = similarity_threshold

    def is_spam(self, text: str) -> Tuple[bool, str]:
        """
        Detects if text contains promotional spam, referral links, or financial advice fraud.
        """
        for pattern, reason in SPAM_PATTERNS:
            if pattern.search(text):
                return True, reason
        return False, ""

    def clean_and_deduplicate(self, raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes a list of raw feedback records:
        1. Checks for spam / bots
        2. Exact deduplication via normalized text hash
        3. Near-duplicate deduplication via RapidFuzz token sort ratio
        4. Detects language (en, hi, hinglish)
        5. Produces normalized cleaned text

        Returns:
            Dict containing:
                "cleaned_items": List[Dict] (records ready for CleanedFeedback table)
                "stats": Funnel counts and metrics
        """
        seen_exact_hashes: Dict[str, str] = {}  # text_hash -> master_id
        processed_candidates: List[Tuple[str, str, str]] = []  # (id, normalized_text, raw_text)
        
        cleaned_records = []
        exact_dupes_count = 0
        near_dupes_count = 0
        spam_count = 0

        for item in raw_items:
            item_id = item["id"]
            raw_text = item["raw_text"].strip()
            
            # Check Spam
            is_spam_item, spam_reason = self.is_spam(raw_text)
            if is_spam_item:
                spam_count += 1
                cleaned_records.append({
                    "id": item_id,
                    "source": item["source"],
                    "app_name": item.get("app_name"),
                    "url": item["url"],
                    "author_hash": item["author_hash"],
                    "date": item["date"],
                    "rating": item.get("rating"),
                    "language": detect_language(raw_text),
                    "raw_text": raw_text,
                    "cleaned_text": raw_text,
                    "is_duplicate": False,
                    "duplicate_of": None,
                    "is_spam": True,
                    "spam_reason": spam_reason,
                    "parent_id": item.get("parent_id"),
                    "upvotes_likes": item.get("upvotes_likes", 0),
                })
                continue

            normalized = normalize_text_for_dedupe(raw_text)
            if not normalized or len(normalized) < 5:
                # Text is too short to be substantive
                continue

            # Exact Deduplication
            exact_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if exact_hash in seen_exact_hashes:
                exact_dupes_count += 1
                cleaned_records.append({
                    "id": item_id,
                    "source": item["source"],
                    "app_name": item.get("app_name"),
                    "url": item["url"],
                    "author_hash": item["author_hash"],
                    "date": item["date"],
                    "rating": item.get("rating"),
                    "language": detect_language(raw_text),
                    "raw_text": raw_text,
                    "cleaned_text": raw_text,
                    "is_duplicate": True,
                    "duplicate_of": seen_exact_hashes[exact_hash],
                    "is_spam": False,
                    "spam_reason": None,
                    "parent_id": item.get("parent_id"),
                    "upvotes_likes": item.get("upvotes_likes", 0),
                })
                continue

            # Near-duplicate check against previous non-duplicate items
            # Compare only against candidates with similar word count
            is_near_dup = False
            master_dup_id = None
            norm_len = len(normalized)

            for cand_id, cand_norm, _ in processed_candidates:
                # Length heuristic optimization
                if abs(len(cand_norm) - norm_len) > 0.3 * max(len(cand_norm), norm_len):
                    continue

                sim_ratio = fuzz.token_sort_ratio(normalized, cand_norm)
                if sim_ratio >= self.similarity_threshold:
                    is_near_dup = True
                    master_dup_id = cand_id
                    break

            if is_near_dup:
                near_dupes_count += 1
                cleaned_records.append({
                    "id": item_id,
                    "source": item["source"],
                    "app_name": item.get("app_name"),
                    "url": item["url"],
                    "author_hash": item["author_hash"],
                    "date": item["date"],
                    "rating": item.get("rating"),
                    "language": detect_language(raw_text),
                    "raw_text": raw_text,
                    "cleaned_text": raw_text,
                    "is_duplicate": True,
                    "duplicate_of": master_dup_id,
                    "is_spam": False,
                    "spam_reason": None,
                    "parent_id": item.get("parent_id"),
                    "upvotes_likes": item.get("upvotes_likes", 0),
                })
                continue

            # Item is unique and non-spam
            seen_exact_hashes[exact_hash] = item_id
            processed_candidates.append((item_id, normalized, raw_text))

            # Detect language and generate normalized cleaned text
            lang = detect_language(raw_text)
            cleaned_text = normalize_hinglish_terms(raw_text)

            cleaned_records.append({
                "id": item_id,
                "source": item["source"],
                "app_name": item.get("app_name"),
                "url": item["url"],
                "author_hash": item["author_hash"],
                "date": item["date"],
                "rating": item.get("rating"),
                "language": lang,
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                "is_duplicate": False,
                "duplicate_of": None,
                "is_spam": False,
                "spam_reason": None,
                "parent_id": item.get("parent_id"),
                "upvotes_likes": item.get("upvotes_likes", 0),
            })

        unique_clean_count = len(cleaned_records) - (exact_dupes_count + near_dupes_count + spam_count)
        stats = {
            "total_input": len(raw_items),
            "spam_filtered": spam_count,
            "exact_duplicates": exact_dupes_count,
            "near_duplicates": near_dupes_count,
            "clean_unique": unique_clean_count,
            "total_output": len(cleaned_records),
        }

        return {
            "cleaned_items": cleaned_records,
            "stats": stats
        }

