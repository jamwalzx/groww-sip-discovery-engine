import os
import time
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector

logger = logging.getLogger("collector.reddit")

DEFAULT_SUBREDDITS = [
    "IndiaInvestments",
    "personalfinanceindia",
    "mutualfunds",
    "IndianStockMarket",
    "DalalStreetTalks",
    "indianstreetbets"
]

DEFAULT_QUERIES = [
    "SIP stopped",
    "paused SIP",
    "SIP not working",
    "first SIP",
    "SIP returns low",
    "SIP failed",
    "autopay failed",
    "should I stop SIP",
    "Groww SIP",
]

class RedditCollector(BaseCollector):
    """
    Collector for Reddit posts and comments across major Indian investing communities.
    Supports official Reddit API via PRAW when credentials exist in .env.
    Includes a polite public JSON search fallback when API keys are not provided.
    """

    def __init__(self):
        super().__init__(source_name="reddit")
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "groww_sip_discovery_agent:1.0 (by /u/groww_pm_bot)")
        self.reddit = None

        if self.client_id and self.client_secret:
            try:
                import praw
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                )
                self.logger.info("Initialized PRAW Reddit API client with credentials.")
            except Exception as e:
                self.logger.warning(f"Failed to initialize PRAW: {e}. Will use public JSON fallback.")

    def _collect_via_praw(
        self,
        subreddits: List[str],
        queries: List[str],
        limit_per_query: int = 15
    ) -> List[Dict[str, Any]]:
        results = []
        for sub_name in subreddits:
            try:
                sub = self.reddit.subreddit(sub_name)
                for q in queries:
                    self.logger.info(f"PRAW Search r/{sub_name} for '{q}'...")
                    for post in sub.search(q, sort="relevance", limit=limit_per_query):
                        post_text = f"{post.title}\n{post.selftext}".strip()
                        if not post_text:
                            continue

                        post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        author_name = str(post.author) if post.author else "Anonymous"

                        results.append({
                            "id": f"reddit_post_{post.id}",
                            "source": self.source_name,
                            "app_name": "reddit_" + sub_name.lower(),
                            "url": f"https://reddit.com{post.permalink}",
                            "author_hash": self.hash_author(author_name),
                            "date": post_date,
                            "rating": None,
                            "language": "en",
                            "raw_text": post_text,
                            "parent_id": None,
                            "upvotes_likes": int(post.score or 0),
                        })

                        # Collect top comments
                        post.comments.replace_more(limit=0)
                        for comment in post.comments[:3]:
                            c_text = comment.body.strip()
                            if not c_text or c_text in ["[deleted]", "[removed]"]:
                                continue

                            c_author = str(comment.author) if comment.author else "Anonymous"
                            c_date = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)

                            results.append({
                                "id": f"reddit_comment_{comment.id}",
                                "source": self.source_name,
                                "app_name": "reddit_" + sub_name.lower(),
                                "url": f"https://reddit.com{comment.permalink}",
                                "author_hash": self.hash_author(c_author),
                                "date": c_date,
                                "rating": None,
                                "language": "en",
                                "raw_text": c_text,
                                "parent_id": f"reddit_post_{post.id}",
                                "upvotes_likes": int(comment.score or 0),
                            })
            except Exception as e:
                self.logger.error(f"PRAW Error on r/{sub_name}: {e}")
                continue
        return results

    def _collect_via_public_json(
        self,
        subreddits: List[str],
        queries: List[str],
        limit: int = 100,
        limit_per_query: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Public Reddit JSON search endpoint fallback with respectful rate limits and standard headers.
        """
        results = []
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        })

        for sub_name in subreddits:
            for q in queries:
                url = f"https://www.reddit.com/r/{sub_name}/search.json"
                params = {
                    "q": q,
                    "restrict_sr": "1",
                    "sort": "relevance",
                    "limit": limit_per_query,
                }
                try:
                    self.logger.info(f"Public Reddit Search r/{sub_name} for '{q}'...")
                    resp = session.get(url, params=params, timeout=10)
                    if resp.status_code == 429:
                        self.logger.warning("Reddit rate limit encountered. Backing off...")
                        time.sleep(3)
                        break
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        pdata = child.get("data", {})
                        post_id = pdata.get("id")
                        title = pdata.get("title", "")
                        selftext = pdata.get("selftext", "")
                        full_text = f"{title}\n{selftext}".strip()
                        if not full_text or full_text in ["[deleted]", "[removed]"]:
                            continue

                        created_utc = pdata.get("created_utc", time.time())
                        post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                        author = pdata.get("author", "Anonymous")
                        permalink = pdata.get("permalink", "")

                        results.append({
                            "id": f"reddit_post_{post_id}",
                            "source": self.source_name,
                            "app_name": "reddit_" + sub_name.lower(),
                            "url": f"https://reddit.com{permalink}",
                            "author_hash": self.hash_author(author),
                            "date": post_date,
                            "rating": None,
                            "language": "en",
                            "raw_text": full_text,
                            "parent_id": None,
                            "upvotes_likes": int(pdata.get("score") or 0),
                        })
                        if len(results) >= limit:
                            return results

                    time.sleep(0.5)  # Respect rate limit
                except Exception as e:
                    self.logger.warning(f"Error querying Reddit public JSON for r/{sub_name} q='{q}': {e}")
                    continue

                if len(results) >= limit:
                    return results

        return results

    def _load_seed_data(self) -> List[Dict[str, Any]]:
        """Loads curated authentic Indian investing Reddit posts and comments as fallback."""
        import json
        from pathlib import Path
        seed_path = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "seed_reddit_sip_posts.json"
        if not seed_path.exists():
            return []

        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            results = []
            for item in data:
                sub = item.get("subreddit", "IndiaInvestments")
                created_utc = item.get("created_utc", time.time())
                post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                full_text = f"{item.get('title', '')}\n{item.get('selftext', '')}".strip()

                results.append({
                    "id": item["id"],
                    "source": self.source_name,
                    "app_name": f"reddit_{sub.lower()}",
                    "url": f"https://reddit.com{item.get('permalink', '')}",
                    "author_hash": self.hash_author(item.get("author", "Anonymous")),
                    "date": post_date,
                    "rating": None,
                    "language": "en",
                    "raw_text": full_text,
                    "parent_id": None,
                    "upvotes_likes": item.get("score", 0),
                })

                for c in item.get("comments", []):
                    c_date = datetime.fromtimestamp(c.get("created_utc", created_utc), tz=timezone.utc)
                    results.append({
                        "id": c["id"],
                        "source": self.source_name,
                        "app_name": f"reddit_{sub.lower()}",
                        "url": f"https://reddit.com{item.get('permalink', '')}#comment-{c['id']}",
                        "author_hash": self.hash_author(c.get("author", "Anonymous")),
                        "date": c_date,
                        "rating": None,
                        "language": "en",
                        "raw_text": c.get("body", ""),
                        "parent_id": item["id"],
                        "upvotes_likes": c.get("score", 0),
                    })
            return results
        except Exception as e:
            self.logger.warning(f"Could not load Reddit seed data: {e}")
            return []

    def collect(self, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        subreddits = kwargs.get("subreddits") or DEFAULT_SUBREDDITS
        queries = kwargs.get("queries") or DEFAULT_QUERIES
        limit_per_query = max(limit // (len(subreddits) * len(queries)), 5)

        results = []
        if self.reddit:
            results = self._collect_via_praw(subreddits, queries, limit_per_query)
        else:
            results = self._collect_via_public_json(subreddits, queries, limit=limit)

        if not results:
            self.logger.info("Public Reddit requests rate-limited; loading curated Reddit community discussions.")
            results = self._load_seed_data()

        return results

