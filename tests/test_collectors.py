import pytest
from datetime import datetime, timezone
from src.collectors.base import BaseCollector
from src.db.models import RawFeedback
from src.db.database import Base, engine, SessionLocal

class DummyCollector(BaseCollector):
    def collect(self, limit: int = 100, **kwargs):
        return []

def test_author_hashing_anonymity():
    collector = DummyCollector(source_name="test")
    
    # Test SHA-256 hash length and properties
    hash1 = collector.hash_author("john_doe_investor")
    hash2 = collector.hash_author("john_doe_investor")
    hash3 = collector.hash_author("different_user")
    anon_hash = collector.hash_author(None)

    assert len(hash1) == 64
    assert hash1 == hash2  # Deterministic for cohort tracking
    assert hash1 != hash3  # Distinct for different users
    assert len(anon_hash) == 64
    assert "john_doe" not in hash1  # Zero PII leakage

def test_raw_feedback_model():
    now = datetime.now(timezone.utc)
    item = RawFeedback(
        id="test_play_123",
        source="play_store",
        app_name="groww",
        url="https://play.google.com/store/apps/details?id=com.nextbillion.groww",
        author_hash="a" * 64,
        date=now,
        rating=5,
        language="en",
        raw_text="Excellent SIP experience on Groww so far.",
        parent_id=None,
        upvotes_likes=10,
    )

    d = item.to_dict()
    assert d["id"] == "test_play_123"
    assert d["source"] == "play_store"
    assert d["app_name"] == "groww"
    assert d["rating"] == 5
    assert len(d["author_hash"]) == 64
    assert "SIP experience" in d["raw_text"]

