import os
import logging
from tabulate import tabulate
from sqlalchemy import func

from src.config import DATABASE_PATH, RAW_DATA_DIR
from src.db.database import init_db, get_db
from src.db.models import RawFeedback, CleanedFeedback
from src.collectors import (
    PlayStoreCollector,
    AppStoreCollector,
    RedditCollector,
    YouTubeCollector,
    ManualImporter,
)
from src.pipeline.cleaner import DataCleaner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_phase2")

from datetime import datetime, timezone

def save_raw_records(records):
    """Saves newly scraped records into raw_feedback table with idempotency."""
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

def save_cleaned_records(cleaned_items):
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

def run_phase2():
    logger.info("Initializing SQLite database tables...")
    init_db()

    # 1. Run Community Collectors
    logger.info("--- Step 1: Ingesting Community & Manual Sources ---")
    
    # Reddit
    reddit_collector = RedditCollector()
    reddit_records = reddit_collector.collect(limit=30)
    ins_red, skip_red = save_raw_records(reddit_records)
    logger.info(f"Reddit: {ins_red} new records, {skip_red} skipped.")

    # YouTube
    yt_collector = YouTubeCollector()
    yt_records = yt_collector.collect(limit=20)
    ins_yt, skip_yt = save_raw_records(yt_records)
    logger.info(f"YouTube: {ins_yt} new records, {skip_yt} skipped.")

    # Manual Importer
    sample_csv_path = RAW_DATA_DIR / "sample_manual_sip_data.csv"
    if sample_csv_path.exists():
        importer = ManualImporter()
        with open(sample_csv_path, "r", encoding="utf-8") as f:
            manual_records = importer.import_from_csv(f.read())
        ins_man, skip_man = save_raw_records(manual_records)
        logger.info(f"Manual CSV Import: {ins_man} new records, {skip_man} skipped.")

    # 2. Fetch all raw items for Cleaning & Deduplication
    logger.info("--- Step 2: Running Cleaner & Deduplication Pipeline ---")
    with get_db() as db:
        all_raw = db.query(RawFeedback).all()
        raw_dicts = [r.to_dict() for r in all_raw]

    cleaner = DataCleaner(similarity_threshold=90.0)
    cleaned_result = cleaner.clean_and_deduplicate(raw_dicts)
    cleaned_items = cleaned_result["cleaned_items"]
    stats = cleaned_result["stats"]

    # 3. Save into cleaned_feedback table
    ins_c, upd_c = save_cleaned_records(cleaned_items)
    logger.info(f"CleanedFeedback Table: {ins_c} inserted, {upd_c} updated.")

    # 4. Display Phase 2 Summary Reports
    display_phase2_reports(stats)

def display_phase2_reports(stats):
    with get_db() as db:
        # Per source breakdown
        source_counts = (
            db.query(RawFeedback.source, func.count(RawFeedback.id))
            .group_by(RawFeedback.source)
            .all()
        )

        # Language breakdown in cleaned feedback
        lang_counts = (
            db.query(CleanedFeedback.language, func.count(CleanedFeedback.id))
            .filter(CleanedFeedback.is_duplicate == False, CleanedFeedback.is_spam == False)
            .group_by(CleanedFeedback.language)
            .all()
        )

    print("\n" + "=" * 70)
    print("                 PHASE 2: INGESTION & CLEANING FUNNEL")
    print("=" * 70)

    print("\n[A] Multi-Source Ingestion Breakdown:")
    source_table = [[s, count] for s, count in source_counts]
    print(tabulate(source_table, headers=["Source Channel", "Raw Items Ingested"], tablefmt="github"))

    print("\n[B] Data Cleaning & Deduplication Funnel:")
    funnel_table = [
        ["Total Raw Ingested", stats["total_input"], "100.0%"],
        ["Spam / Bot / Referral Filtered", stats["spam_filtered"], f"{(stats['spam_filtered']/max(stats['total_input'],1))*100:.1f}%"],
        ["Exact Duplicates Pruned", stats["exact_duplicates"], f"{(stats['exact_duplicates']/max(stats['total_input'],1))*100:.1f}%"],
        ["Near-Duplicates Pruned (>90%)", stats["near_duplicates"], f"{(stats['near_duplicates']/max(stats['total_input'],1))*100:.1f}%"],
        ["Clean & Unique Records Ready for Extraction", stats["clean_unique"], f"{(stats['clean_unique']/max(stats['total_input'],1))*100:.1f}%"],
    ]
    print(tabulate(funnel_table, headers=["Funnel Stage", "Item Count", "Share"], tablefmt="github"))

    print("\n[C] Language Distribution (Cleaned Unique Items):")
    lang_labels = {"en": "English", "hi": "Hindi (Devanagari)", "hinglish": "Hinglish (Colloquial)"}
    lang_table = [[lang_labels.get(l, l), cnt] for l, cnt in lang_counts]
    print(tabulate(lang_table, headers=["Detected Language", "Count"], tablefmt="github"))

    print("-" * 70)
    print(f"Database Location   : {DATABASE_PATH}")
    print("Pipeline Status     : PHASE 2 SUCCESS")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_phase2()

