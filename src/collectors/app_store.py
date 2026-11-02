import time
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector
from src.config import MONITORED_APPS

logger = logging.getLogger(__name__)

class AppStoreCollector(BaseCollector):
    """
    Collector for Apple App Store customer reviews across Groww and competitor wealth apps in India.
    Uses Apple's public iTunes Customer Reviews RSS/JSON API for the India ('in') storefront.
    """

    def __init__(self):
        super().__init__(source_name="app_store")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
        })

    def collect_for_app(self, app_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Collect reviews for a single configured iOS app via iTunes RSS JSON API.
        """
        if app_key not in MONITORED_APPS:
            self.logger.warning(f"App key '{app_key}' not in MONITORED_APPS")
            return []

        app_meta = MONITORED_APPS[app_key]
        app_id = app_meta.get("app_store_id")
        if not app_id:
            self.logger.warning(f"No app_store_id configured for {app_key}")
            return []

        results: List[Dict[str, Any]] = []
        max_pages = min((limit + 49) // 50, 10)  # Apple RSS serves up to 50 items/page, max 10 pages

        for page in range(1, max_pages + 1):
            url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
            try:
                self.logger.info(
                    f"Fetching App Store reviews for {app_meta['name']} (ID: {app_id}) [page {page}/{max_pages}]"
                )
                response = self.session.get(url, timeout=10)
                if response.status_code == 404 or response.status_code == 400:
                    self.logger.info(f"Reached end of reviews for {app_key} on page {page}")
                    break
                if response.status_code != 200:
                    self.logger.warning(
                        f"Non-200 status {response.status_code} from App Store API for {app_key}"
                    )
                    break

                data = response.json()
                feed = data.get("feed", {})
                entries = feed.get("entry", [])
                
                # In iTunes RSS JSON, the first entry is often the app metadata itself if page==1
                if isinstance(entries, dict):
                    entries = [entries]

                page_items_added = 0
                for entry in entries:
                    # Skip application metadata entry (has 'im:name' instead of 'author')
                    if "im:name" in entry and "author" not in entry:
                        continue

                    review_id = entry.get("id", {}).get("label")
                    if not review_id:
                        continue

                    author_name = entry.get("author", {}).get("name", {}).get("label", "Anonymous")
                    rating_str = entry.get("im:rating", {}).get("label", "0")
                    rating = int(rating_str) if rating_str.isdigit() else None

                    title = entry.get("title", {}).get("label", "").strip()
                    content = entry.get("content", {}).get("label", "").strip()
                    full_text = f"{title}\n{content}".strip() if title and title not in content else (content or title)

                    if not full_text:
                        continue

                    # Parse date: e.g. "2026-10-15T09:22:45-07:00"
                    updated_str = entry.get("updated", {}).get("label")
                    try:
                        if updated_str:
                            review_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                        else:
                            review_date = datetime.now(timezone.utc)
                    except Exception:
                        review_date = datetime.now(timezone.utc)

                    item = {
                        "id": f"appstore_{app_key}_{review_id}",
                        "source": self.source_name,
                        "app_name": app_key,
                        "url": f"https://apps.apple.com/in/app/id{app_id}",
                        "author_hash": self.hash_author(author_name),
                        "date": review_date,
                        "rating": rating,
                        "language": "en",  # Default store language; language module will refine in Phase 2
                        "raw_text": full_text,
                        "parent_id": None,
                        "upvotes_likes": 0,
                    }
                    results.append(item)
                    page_items_added += 1

                    if len(results) >= limit:
                        break

                if len(results) >= limit or page_items_added == 0:
                    break

                # Respect rate limits
                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error fetching App Store reviews for {app_key} (page {page}): {e}")
                break

        return results

    def collect(self, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Collect reviews across all configured monitored iOS apps.
        """
        apps_to_scrape = kwargs.get("apps") or list(MONITORED_APPS.keys())
        per_app_limit = max(limit // len(apps_to_scrape), 20)

        all_results = []
        for app_key in apps_to_scrape:
            app_results = self.collect_for_app(app_key=app_key, limit=per_app_limit)
            all_results.extend(app_results)

        return all_results
