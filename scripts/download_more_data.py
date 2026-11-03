"""
Download More Reviews & Comments: Multi-Source Harvester

Fetches fresh real-world reviews and discussions across:
1. Google Play Store (Groww, Zerodha Coin, INDmoney, Kuvera, ET Money, Paytm Money) in English & Hindi
2. Apple App Store (India Storefront)
3. YouTube Data API v3 (Live personal finance & beginner SIP comment streams)
4. Reddit (r/IndiaInvestments, r/mutualfunds, r/personalfinanceindia)

Automatically deduplicates, cleans, and updates the local SQLite database (data/app.db).
Optionally runs downstream Phase 3 (LLM Extraction) and Phase 4-5 (Opportunity Matrix & Clustering).
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone
from tabulate import tabulate
from sqlalchemy import func

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import MONITORED_APPS, DATABASE_PATH, RAW_DATA_DIR
from src.db.database import init_db, get_db
from src.db.models import RawFeedback, CleanedFeedback, ExtractedInsight, Theme
from src.collectors.play_store import PlayStoreCollector
from src.collectors.app_store import AppStoreCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.reddit import RedditCollector
from src.pipeline.cleaner import DataCleaner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("download_more_data")


def save_raw_batch(records):
    """Saves raw scraped records into SQLite raw_feedback table with duplicate rejection."""
    if not records:
        return 0, 0

    inserted = 0
    skipped = 0
    with get_db() as db:
        for rec in records:
            existing = db.query(RawFeedback.id).filter(RawFeedback.id == rec["id"]).first()
            if existing:
                skipped += 1
                continue

            rec_date = rec["date"]
            if isinstance(rec_date, str):
                try:
                    rec_date = datetime.fromisoformat(rec_date.replace("Z", "+00:00"))
                except Exception:
                    rec_date = datetime.now(timezone.utc)

            fb = RawFeedback(
                id=rec["id"],
                source=rec["source"],
                app_name=rec.get("app_name"),
                url=rec["url"],
                author_hash=rec["author_hash"],
                date=rec_date,
                rating=rec.get("rating"),
                language=rec.get("language", "unknown"),
                raw_text=rec["raw_text"],
                parent_id=rec.get("parent_id"),
                upvotes_likes=rec.get("upvotes_likes", 0),
            )
            db.add(fb)
            inserted += 1

    return inserted, skipped


def save_cleaned_batch(cleaned_items):
    """Saves cleaned and deduplicated records into cleaned_feedback table."""
    inserted = 0
    updated = 0
    with get_db() as db:
        for item in cleaned_items:
            item_date = item["date"]
            if isinstance(item_date, str):
                try:
                    item_date = datetime.fromisoformat(item_date.replace("Z", "+00:00"))
                except Exception:
                    item_date = datetime.now(timezone.utc)

            existing = db.query(CleanedFeedback).filter(CleanedFeedback.id == item["id"]).first()
            if existing:
                existing.language = item["language"]
                existing.cleaned_text = item["cleaned_text"]
                existing.is_duplicate = item["is_duplicate"]
                existing.duplicate_of = item["duplicate_of"]
                existing.is_spam = item["is_spam"]
                existing.spam_reason = item["spam_reason"]
                updated += 1
            else:
                cf = CleanedFeedback(
                    id=item["id"],
                    source=item["source"],
                    app_name=item.get("app_name"),
                    url=item["url"],
                    author_hash=item["author_hash"],
                    date=item_date,
                    rating=item.get("rating"),
                    language=item["language"],
                    raw_text=item["raw_text"],
                    cleaned_text=item["cleaned_text"],
                    is_duplicate=item["is_duplicate"],
                    duplicate_of=item["duplicate_of"],
                    is_spam=item["is_spam"],
                    spam_reason=item["spam_reason"],
                    parent_id=item.get("parent_id"),
                    upvotes_likes=item.get("upvotes_likes", 0),
                )
                db.add(cf)
                inserted += 1

    return inserted, updated


def harvest_data(play_limit=40, app_limit=30, yt_limit=30, reddit_limit=20):
    """
    Orchestrates ingestion across all available collectors.
    """
    logger.info("=" * 60)
    logger.info("Starting Multi-Source Data Collection")
    logger.info("=" * 60)

    stats = {}

    # 1. Google Play Store
    try:
        logger.info(f"[1/4] Scraping Google Play Store (target: {play_limit} per app across 6 apps)...")
        play_collector = PlayStoreCollector()
        all_play = []
        for app_key in MONITORED_APPS.keys():
            recs = play_collector.collect_for_app(app_key=app_key, limit=play_limit)
            all_play.extend(recs)
        ins_p, skip_p = save_raw_batch(all_play)
        stats["Google Play Store"] = (len(all_play), ins_p, skip_p)
        logger.info(f"Play Store: {ins_p} new records inserted, {skip_p} existing skipped.")
    except Exception as e:
        logger.error(f"Play Store collection error: {e}")
        stats["Google Play Store"] = (0, 0, 0)

    # 2. Apple App Store
    try:
        logger.info(f"[2/4] Scraping Apple App Store (target: {app_limit} per app across 6 apps)...")
        app_collector = AppStoreCollector()
        all_app = []
        for app_key in MONITORED_APPS.keys():
            recs = app_collector.collect_for_app(app_key=app_key, limit=app_limit)
            all_app.extend(recs)
        ins_a, skip_a = save_raw_batch(all_app)
        stats["Apple App Store"] = (len(all_app), ins_a, skip_a)
        logger.info(f"Apple App Store: {ins_a} new records inserted, {skip_a} existing skipped.")
    except Exception as e:
        logger.error(f"App Store collection error: {e}")
        stats["Apple App Store"] = (0, 0, 0)

    # 3. YouTube Data API v3
    try:
        logger.info("[3/4] Ingesting YouTube Personal Finance Comments...")
        yt_collector = YouTubeCollector()
        queries = [
            "Groww SIP mutual funds beginner",
            "SIP autopay failed Groww",
            "Mutual fund negative returns what to do",
            "How to stop or pause Groww SIP",
            "Parag Parikh Flexi Cap SIP review Groww"
        ]
        yt_records = yt_collector.collect(limit=yt_limit, queries=queries)
        ins_y, skip_y = save_raw_batch(yt_records)
        stats["YouTube Comments"] = (len(yt_records), ins_y, skip_y)
        logger.info(f"YouTube: {ins_y} new records inserted, {skip_y} existing skipped.")
    except Exception as e:
        logger.error(f"YouTube collection error: {e}")
        stats["YouTube Comments"] = (0, 0, 0)

    # 4. Reddit
    try:
        logger.info(f"[4/4] Ingesting Reddit Investment Communities (limit: {reddit_limit})...")
        reddit_collector = RedditCollector()
        reddit_records = reddit_collector.collect(
            limit=reddit_limit,
            subreddits=["IndiaInvestments", "mutualfunds"],
            queries=["Groww SIP", "SIP stopped", "autopay failed"]
        )
        ins_r, skip_r = save_raw_batch(reddit_records)
        stats["Reddit Discussions"] = (len(reddit_records), ins_r, skip_r)
        logger.info(f"Reddit: {ins_r} new records inserted, {skip_r} existing skipped.")
    except Exception as e:
        logger.error(f"Reddit collection error: {e}")
        stats["Reddit Discussions"] = (0, 0, 0)

    # 5. Clean & Deduplicate All Raw Items
    logger.info("Cleaning and deduplicating raw feedback...")
    with get_db() as db:
        all_raw = db.query(RawFeedback).all()
        raw_dicts = [r.to_dict() for r in all_raw]

    cleaner = DataCleaner(similarity_threshold=90.0)
    cleaned_result = cleaner.clean_and_deduplicate(raw_dicts)
    ins_c, upd_c = save_cleaned_batch(cleaned_result["cleaned_items"])
    logger.info(f"CleanedFeedback: {ins_c} new inserted, {upd_c} updated.")

    return stats, cleaned_result["stats"]


def print_harvest_summary(stats, clean_stats):
    with get_db() as db:
        raw_total = db.query(func.count(RawFeedback.id)).scalar()
        clean_total = db.query(func.count(CleanedFeedback.id)).filter(
            CleanedFeedback.is_duplicate == False, CleanedFeedback.is_spam == False
        ).scalar()
        source_breakdown = (
            db.query(RawFeedback.source, func.count(RawFeedback.id))
            .group_by(RawFeedback.source)
            .all()
        )

    print("\n" + "=" * 70)
    print("           DATA HARVEST & PIPELINE UPDATE REPORT")
    print("=" * 70)

    harvest_table = [
        [src, fetched, inserted, skipped]
        for src, (fetched, inserted, skipped) in stats.items()
    ]
    print(tabulate(harvest_table, headers=["Channel", "Total Fetched", "New Inserted", "Duplicates Skipped"], tablefmt="github"))

    print("\n[Current Database Inventory]:")
    inv_table = [[s, cnt] for s, cnt in source_breakdown]
    print(tabulate(inv_table, headers=["Channel Source", "Total Raw Records"], tablefmt="github"))

    print("-" * 70)
    print(f"Total Raw Records in DB     : {raw_total}")
    print(f"Clean & Unique Records Ready: {clean_total}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Harvest additional real-world reviews & comments for Groww SIP engine")
    parser.add_argument("--play-limit", type=int, default=40, help="Play Store reviews per app (default: 40)")
    parser.add_argument("--app-limit", type=int, default=30, help="App Store reviews per app (default: 30)")
    parser.add_argument("--yt-limit", type=int, default=25, help="YouTube comments per query (default: 25)")
    parser.add_argument("--reddit-limit", type=int, default=15, help="Reddit items total (default: 15)")
    parser.add_argument("--run-downstream", action="store_true", default=False, help="Also run Phase 3-5 extraction & analytics")

    args = parser.parse_args()

    init_db()
    stats, clean_stats = harvest_data(
        play_limit=args.play_limit,
        app_limit=args.app_limit,
        yt_limit=args.yt_limit,
        reddit_limit=args.reddit_limit
    )
    print_harvest_summary(stats, clean_stats)

    if args.run_downstream:
        logger.info("Running downstream Phase 3 Structured Extraction...")
        from scripts.run_phase3_extraction import run_phase3
        run_phase3()

        logger.info("Running downstream Phase 4 Semantic Clustering...")
        from scripts.run_phase4_clustering import run_phase4
        run_phase4()

        logger.info("Running downstream Phase 5 Analytics & Opportunity Matrix...")
        from scripts.run_phase5_analytics import run_phase5
        run_phase5()

        logger.info("Downstream pipeline successfully updated!")


if __name__ == "__main__":
    main()
