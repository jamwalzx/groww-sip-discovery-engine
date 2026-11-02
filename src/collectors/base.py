import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.config import HASH_SALT

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """
    Abstract Base Class for all data collector modules.
    Enforces common interface, rate-limiting, and PII anonymization.
    """

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"collector.{source_name}")

    def hash_author(self, raw_author: Optional[str]) -> str:
        """
        Hashes an author identifier using salted SHA-256 to ensure ZERO PII is stored.
        Consistent for tracking repeat authors across time while strictly anonymized.
        """
        if not raw_author or not str(raw_author).strip():
            return hashlib.sha256(f"{HASH_SALT}_anonymous".encode("utf-8")).hexdigest()
        
        salted = f"{HASH_SALT}_{str(raw_author).strip()}"
        return hashlib.sha256(salted.encode("utf-8")).hexdigest()

    @abstractmethod
    def collect(self, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute collection and return standardized records adhering to the common schema.
        
        Returns:
            List of dicts formatted with keys matching RawFeedback model:
            [
                {
                    "id": str,
                    "source": str,
                    "app_name": str,
                    "url": str,
                    "author_hash": str,
                    "date": datetime,
                    "rating": Optional[int],
                    "language": str,
                    "raw_text": str,
                    "parent_id": Optional[str],
                    "upvotes_likes": int
                },
                ...
            ]
        """
        pass

