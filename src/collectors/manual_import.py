import io
import csv
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Union
from src.collectors.base import BaseCollector

logger = logging.getLogger("collector.manual_import")

class ManualImporter(BaseCollector):
    """
    Universal fallback importer for CSV, JSON, and raw pasted text.
    Enables users to import data collected from restricted platforms (e.g. X/Twitter,
    Telegram groups, internal spreadsheets, or custom user interviews).
    """

    def __init__(self):
        super().__init__(source_name="manual_import")

    def import_from_csv(self, file_content: Union[str, io.StringIO]) -> List[Dict[str, Any]]:
        """
        Parses CSV data into common schema. Supports standard headers:
        text / comment / review / content, author, date, rating, url, source
        """
        results = []
        if isinstance(file_content, str):
            f = io.StringIO(file_content)
        else:
            f = file_content

        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Find text content column
            raw_text = (
                row.get("raw_text") or row.get("text") or row.get("comment") or
                row.get("review") or row.get("content") or ""
            ).strip()

            if not raw_text:
                continue

            author = row.get("author") or row.get("user") or row.get("username") or f"user_{idx}"
            date_str = row.get("date") or row.get("created_at") or row.get("timestamp")
            try:
                if date_str:
                    item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    item_date = datetime.now(timezone.utc)
            except Exception:
                item_date = datetime.now(timezone.utc)

            rating_val = row.get("rating") or row.get("score")
            try:
                rating = int(rating_val) if rating_val is not None and str(rating_val).isdigit() else None
            except Exception:
                rating = None

            item_id = row.get("id") or f"manual_csv_{hash(raw_text) % 10000000}_{idx}"
            url = row.get("url") or "https://manual-import.groww.internal/item/" + str(item_id)
            app_name = row.get("app_name") or row.get("app") or "groww"
            upvotes = int(row.get("upvotes") or row.get("likes") or 0)

            results.append({
                "id": str(item_id),
                "source": self.source_name,
                "app_name": app_name,
                "url": url,
                "author_hash": self.hash_author(author),
                "date": item_date,
                "rating": rating,
                "language": "en",
                "raw_text": raw_text,
                "parent_id": row.get("parent_id"),
                "upvotes_likes": upvotes,
            })

        return results

    def import_from_json(self, json_content: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Parses JSON array of feedback records into common schema.
        """
        if isinstance(json_content, str):
            data = json.loads(json_content)
        else:
            data = json_content

        if not isinstance(data, list):
            data = [data]

        results = []
        for idx, row in enumerate(data):
            raw_text = (
                row.get("raw_text") or row.get("text") or row.get("comment") or
                row.get("review") or row.get("content") or ""
            ).strip()

            if not raw_text:
                continue

            author = row.get("author") or f"user_{idx}"
            date_str = row.get("date")
            try:
                if date_str:
                    item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    item_date = datetime.now(timezone.utc)
            except Exception:
                item_date = datetime.now(timezone.utc)

            item_id = row.get("id") or f"manual_json_{hash(raw_text) % 10000000}_{idx}"
            results.append({
                "id": str(item_id),
                "source": self.source_name,
                "app_name": row.get("app_name", "groww"),
                "url": row.get("url", f"https://manual-import.groww.internal/json/{item_id}"),
                "author_hash": self.hash_author(author),
                "date": item_date,
                "rating": row.get("rating"),
                "language": row.get("language", "en"),
                "raw_text": raw_text,
                "parent_id": row.get("parent_id"),
                "upvotes_likes": int(row.get("upvotes_likes", 0)),
            })

        return results

    def import_from_raw_paste(self, text: str, app_name: str = "groww") -> List[Dict[str, Any]]:
        """
        Splits arbitrary pasted multiline text (e.g. forum thread or interview quotes separated by double newlines)
        into individual records.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        results = []
        now = datetime.now(timezone.utc)

        for idx, p in enumerate(paragraphs):
            item_id = f"manual_paste_{abs(hash(p)) % 10000000}_{idx}"
            results.append({
                "id": item_id,
                "source": self.source_name,
                "app_name": app_name,
                "url": f"https://manual-import.groww.internal/paste/{item_id}",
                "author_hash": self.hash_author(f"pasted_author_{idx}"),
                "date": now,
                "rating": None,
                "language": "en",
                "raw_text": p,
                "parent_id": None,
                "upvotes_likes": 0,
            })

        return results

    def collect(self, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        # Default collect returns empty unless input file/text is supplied
        csv_path = kwargs.get("csv_path")
        if csv_path:
            with open(csv_path, "r", encoding="utf-8") as f:
                return self.import_from_csv(f.read())
        return []

