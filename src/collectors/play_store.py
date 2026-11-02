import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector
from src.config import MONITORED_APPS

try:
    from google_play_scraper import reviews, Sort
except ImportError:
    reviews = None
    Sort = None

logger = logging.getLogger(__name__)

class PlayStoreCollector(BaseCollector):
    """
    Collector for Google Play Store user reviews across Groww and competing wealth platforms.
    Filters specifically for India (country='in') and supports English ('en') and Hindi ('hi').
    """

    def __init__(self):
        super().__init__(source_name="play_store")

    def collect_for_app(
        self,
        app_key: str,
        limit: int = 100,
        languages: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect reviews for a single configured app.
        """
        if reviews is None:
            self.logger.error("google-play-scraper package is not installed.")
            return []

        if app_key not in MONITORED_APPS:
            self.logger.warning(f"App key '{app_key}' not in MONITORED_APPS")
            return []

        app_meta = MONITORED_APPS[app_key]
        package_id = app_meta["play_store_id"]
        languages = languages or ["en", "hi"]
        
        results: List[Dict[str, Any]] = []
        per_lang_limit = max(limit // len(languages), 10)

        for lang in languages:
            try:
                self.logger.info(
                    f"Fetching Play Store reviews for {app_meta['name']} ({package_id}) "
                    f"[lang={lang}, country=in, limit={per_lang_limit}]"
                )
                scraped_reviews, _ = reviews(
                    package_id,
                    lang=lang,
                    country="in",
                    sort=Sort.NEWEST,
                    count=per_lang_limit,
                    filter_score_with=None  # fetch all scores 1-5
                )

                for rev in scraped_reviews:
                    review_id = str(rev.get("reviewId") or rev.get("id") or hash(rev.get("content", "")))
                    author_name = rev.get("userName")
                    review_date = rev.get("at")
                    if isinstance(review_date, datetime):
                        if review_date.tzinfo is None:
                            review_date = review_date.replace(tzinfo=timezone.utc)
                    else:
                        review_date = datetime.now(timezone.utc)

                    content = str(rev.get("content") or "").strip()
                    if not content:
                        continue

                    item = {
                        "id": f"play_{app_key}_{review_id}",
                        "source": self.source_name,
                        "app_name": app_key,
                        "url": f"https://play.google.com/store/apps/details?id={package_id}",
                        "author_hash": self.hash_author(author_name),
                        "date": review_date,
                        "rating": int(rev.get("score") or 0),
                        "language": lang,
                        "raw_text": content,
                        "parent_id": None,
                        "upvotes_likes": int(rev.get("thumbsUpCount") or 0),
                    }
                    results.append(item)

            except Exception as e:
                self.logger.error(
                    f"Error scraping Play Store for app '{app_key}' ({package_id}) in '{lang}': {e}"
                )
                continue

        return results

    def collect(self, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Collect reviews across all configured monitored apps.
        limit: target total or per-app limit based on kwargs.
        """
        apps_to_scrape = kwargs.get("apps") or list(MONITORED_APPS.keys())
        per_app_limit = max(limit // len(apps_to_scrape), 20)
        
        all_results = []
        for app_key in apps_to_scrape:
            app_results = self.collect_for_app(app_key=app_key, limit=per_app_limit)
            all_results.extend(app_results)

        return all_results

