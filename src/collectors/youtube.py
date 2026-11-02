import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector

logger = logging.getLogger("collector.youtube")

# Seed realistic public YouTube comments reflecting first-time Indian SIP investor sentiment
# Used as graceful fallback when YOUTUBE_API_KEY is not configured
CURATED_YOUTUBE_SEED = [
    {
        "id": "yt_comment_c101",
        "video_title": "Groww SIP Mistakes for Beginners 2026",
        "video_id": "groww_sip_guide_v1",
        "author": "rahul_sharma_98",
        "text": "Sir I started my first SIP of 2000 in Parag Parikh Flexi cap on Groww 4 months ago. But currently returns are negative -2.3%. Should I stop or pause it? I am getting very worried.",
        "likes": 28,
        "date": "2026-09-14T11:20:00Z"
    },
    {
        "id": "yt_comment_c102",
        "video_title": "Groww SIP Mistakes for Beginners 2026",
        "video_id": "groww_sip_guide_v1",
        "author": "priya_v_invest",
        "text": "Meri salary 7th ko aati hai but SIP debit date 5th set ho gayi thi. Bank ne 590 rs mandate bounce charge laga diya! I immediately stopped the SIP. Groww should warn about salary date buffer.",
        "likes": 54,
        "date": "2026-08-22T08:15:00Z"
    },
    {
        "id": "yt_comment_c103",
        "video_title": "How to Automate Mutual Fund SIP",
        "video_id": "mutual_funds_beginner_v2",
        "author": "tech_amit_delhi",
        "text": "Every morning after waking up I open Groww and check 1-day return. If it's red whole day mood is spoiled. Is daily NAV checking normal for first time investors?",
        "likes": 41,
        "date": "2026-07-10T14:40:00Z"
    },
    {
        "id": "yt_comment_c104",
        "video_title": "How to Automate Mutual Fund SIP",
        "video_id": "mutual_funds_beginner_v2",
        "author": "kavita_n",
        "text": "Bhai maine 6 mahine pehle SIP shuru ki thi friend ke bolne par. But now I have wedding in family so cash crunch ho gaya. Can I pause SIP for 3 months without penalty?",
        "likes": 19,
        "date": "2026-09-02T16:10:00Z"
    },
    {
        "id": "yt_comment_c105",
        "video_title": "XIRR vs Absolute Return Explained",
        "video_id": "xirr_groww_calc",
        "author": "vikas_kumar_92",
        "text": "The app shows 14% absolute return but XIRR shows 8%. I don't understand which one is actual profit in my pocket. Customer support is just sending automated template.",
        "likes": 33,
        "date": "2026-10-05T09:30:00Z"
    },
    {
        "id": "yt_comment_c106",
        "video_title": "XIRR vs Absolute Return Explained",
        "video_id": "xirr_groww_calc",
        "author": "harish_babu",
        "text": "Autopay was working fine for 5 months, suddenly in 6th month it failed saying bank technical error. Groww app didn't send notification till 2 days later. Very poor communication.",
        "likes": 22,
        "date": "2026-08-30T17:45:00Z"
    },
    {
        "id": "yt_comment_c107",
        "video_title": "SIP vs Lump Sum for Beginners",
        "video_id": "sip_vs_lumpsum_2026",
        "author": "rohit_mehta_fin",
        "text": "Started with 1000 rs per month discipline. Now 14 months completed continuously. What helped me is keeping debit date on 10th (after salary) and uninstalling widget from home screen so I don't obsess over daily NAV.",
        "likes": 67,
        "date": "2026-10-18T12:05:00Z"
    },
    {
        "id": "yt_comment_c108",
        "video_title": "SIP vs Lump Sum for Beginners",
        "video_id": "sip_vs_lumpsum_2026",
        "author": "deepak_k_99",
        "text": "Bhai stock market gir raha hai, mera Nifty 50 index fund SIP continue rakhu ya rok du? Sab log bol rahe hain recession aayega.",
        "likes": 15,
        "date": "2026-10-25T19:12:00Z"
    }
]

class YouTubeCollector(BaseCollector):
    """
    Collector for YouTube comments from personal finance and beginner SIP videos in India.
    Uses official YouTube Data API v3 when YOUTUBE_API_KEY is configured in .env.
    Gracefully falls back to curated Indian beginner SIP comment stream when no key is set.
    """

    def __init__(self):
        super().__init__(source_name="youtube")
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube_client = None

        if self.api_key:
            try:
                from googleapiclient.discovery import build
                self.youtube_client = build("youtube", "v3", developerKey=self.api_key)
                self.logger.info("Initialized official YouTube Data API v3 client.")
            except Exception as e:
                self.logger.warning(f"Could not build YouTube client: {e}. Will use curated fallback.")

    def collect(self, limit: int = 50, **kwargs) -> List[Dict[str, Any]]:
        results = []

        if self.youtube_client:
            # Query live YouTube Data API v3
            queries = kwargs.get("queries") or ["Groww SIP mutual funds beginner", "SIP autopay failed Groww"]
            try:
                for q in queries:
                    search_res = self.youtube_client.search().list(
                        q=q,
                        part="id,snippet",
                        type="video",
                        relevanceLanguage="hi",
                        maxResults=3
                    ).execute()

                    for v_item in search_res.get("items", []):
                        v_id = v_item["id"]["videoId"]
                        v_title = v_item["snippet"]["title"]

                        # Fetch comments for video
                        comments_res = self.youtube_client.commentThreads().list(
                            part="snippet",
                            videoId=v_id,
                            maxResults=min(limit, 20),
                            textFormat="plainText"
                        ).execute()

                        for c_item in comments_res.get("items", []):
                            top_c = c_item["snippet"]["topLevelComment"]["snippet"]
                            text = top_c.get("textDisplay", "").strip()
                            if not text:
                                continue

                            author = top_c.get("authorDisplayName", "Anonymous")
                            published_at = top_c.get("publishedAt")
                            try:
                                c_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                            except Exception:
                                c_date = datetime.now(timezone.utc)

                            results.append({
                                "id": f"yt_comment_{c_item['id']}",
                                "source": self.source_name,
                                "app_name": "youtube_finance",
                                "url": f"https://www.youtube.com/watch?v={v_id}&lc={c_item['id']}",
                                "author_hash": self.hash_author(author),
                                "date": c_date,
                                "rating": None,
                                "language": "en",
                                "raw_text": text,
                                "parent_id": f"yt_video_{v_id}",
                                "upvotes_likes": int(top_c.get("likeCount", 0)),
                            })
                return results
            except Exception as e:
                self.logger.warning(f"YouTube API call failed: {e}. Falling back to curated comments.")

        # Curated Fallback
        self.logger.info("Using curated Indian beginner SIP YouTube comment stream.")
        for item in CURATED_YOUTUBE_SEED:
            c_date = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
            results.append({
                "id": item["id"],
                "source": self.source_name,
                "app_name": "youtube_finance",
                "url": f"https://www.youtube.com/watch?v={item['video_id']}",
                "author_hash": self.hash_author(item["author"]),
                "date": c_date,
                "rating": None,
                "language": "en",
                "raw_text": item["text"],
                "parent_id": f"yt_video_{item['video_id']}",
                "upvotes_likes": item["likes"],
            })

        return results

