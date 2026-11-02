import pytest
from datetime import datetime, timezone
from src.pipeline.language import detect_language, normalize_hinglish_terms
from src.pipeline.cleaner import DataCleaner
from src.collectors.manual_import import ManualImporter

def test_language_detection():
    # English
    en_text = "I have been investing in Parag Parikh Flexi Cap SIP for 6 months."
    assert detect_language(en_text) == "en"

    # Hindi (Devanagari)
    hi_text = "ग्रो ऐप पर एसआईपी कैसे शुरू करें? मुझे मदद चाहिए।"
    assert detect_language(hi_text) == "hi"

    # Hinglish
    hinglish_text = "Mera SIP auto debit fail ho gaya aur bank ne mandate bounce charge kat liya. Kya karu?"
    assert detect_language(hinglish_text) == "hinglish"

def test_spam_detection():
    cleaner = DataCleaner()

    # Legitimate investment feedback
    legit_text = "The returns are good but the XIRR calculation is very confusing on the home screen."
    is_sp, reason = cleaner.is_spam(legit_text)
    assert not is_sp

    # Referral promo spam
    promo_text = "Join using my referral code GROWW100 to get free money! Click http://bit.ly/cash"
    is_sp, reason = cleaner.is_spam(promo_text)
    assert is_sp
    assert reason == "referral_code"

    # Telegram scam tips
    tele_text = "For guaranteed 50% profit calls join our telegram channel t.me/stock_gains"
    is_sp, reason = cleaner.is_spam(tele_text)
    assert is_sp
    assert reason == "telegram_promotion"

def test_exact_and_near_deduplication():
    cleaner = DataCleaner(similarity_threshold=90.0)
    now = datetime.now(timezone.utc)

    raw_items = [
        {
            "id": "1",
            "source": "play_store",
            "app_name": "groww",
            "url": "http://example.com/1",
            "author_hash": "a" * 64,
            "date": now,
            "rating": 5,
            "raw_text": "Very smooth app for mutual fund SIP investment in India.",
        },
        # Exact duplicate (different casing and punctuation)
        {
            "id": "2",
            "source": "play_store",
            "app_name": "groww",
            "url": "http://example.com/2",
            "author_hash": "b" * 64,
            "date": now,
            "rating": 5,
            "raw_text": "Very smooth app for mutual fund SIP investment in India!!!",
        },
        # Near-duplicate (>90% token match)
        {
            "id": "3",
            "source": "app_store",
            "app_name": "groww",
            "url": "http://example.com/3",
            "author_hash": "c" * 64,
            "date": now,
            "rating": 5,
            "raw_text": "Very smooth app for mutual fund SIP investment India",
        },
        # Unique item
        {
            "id": "4",
            "source": "reddit",
            "app_name": "groww",
            "url": "http://example.com/4",
            "author_hash": "d" * 64,
            "date": now,
            "rating": 1,
            "raw_text": "Autopay failed without warning and bank charged penalty.",
        },
    ]

    res = cleaner.clean_and_deduplicate(raw_items)
    stats = res["stats"]
    items = res["cleaned_items"]

    assert stats["exact_duplicates"] == 1
    assert stats["near_duplicates"] == 1
    assert stats["clean_unique"] == 2
    assert items[0]["is_duplicate"] is False
    assert items[1]["is_duplicate"] is True
    assert items[1]["duplicate_of"] == "1"
    assert items[2]["is_duplicate"] is True
    assert items[2]["duplicate_of"] == "1"
    assert items[3]["is_duplicate"] is False

def test_manual_importer_csv():
    importer = ManualImporter()
    csv_sample = """text,author,date,rating,app_name,url,upvotes
"Market is down and my SIP is negative. What to do?",user_investor,2026-10-01T12:00:00Z,2,groww,https://example.com,5
"""
    records = importer.import_from_csv(csv_sample)
    assert len(records) == 1
    assert "Market is down" in records[0]["raw_text"]
    assert records[0]["rating"] == 2
    assert len(records[0]["author_hash"]) == 64

