import logging
from tabulate import tabulate
from sqlalchemy import func

from src.config import DATABASE_PATH
from src.db.database import init_db, get_db
from src.db.models import ExtractedInsight, CleanedFeedback, Theme, ItemThemeMapping
from src.ml.embeddings import EmbeddingGenerator
from src.ml.clustering import SemanticClusterer
from src.ml.theme_namer import ThemeNamer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_phase4")

def save_themes_and_mappings(cluster_results, clusterer_obj):
    """
    Saves discovered themes and item-to-theme mappings into SQLite database with idempotency.
    """
    clusters = cluster_results.get("clusters", {})
    outliers = cluster_results.get("outliers", [])
    namer = ThemeNamer()

    with get_db() as db:
        # Clear previous mapping runs for fresh discovery state
        db.query(ItemThemeMapping).delete()
        db.query(Theme).delete()

        discovered_themes_summary = []

        for cid, cdata in clusters.items():
            items = cdata["items"]
            exemplars = cdata.get("exemplars", [])

            # Name cluster using ThemeNamer
            meta = namer.name_cluster(cdata)

            quote_1 = exemplars[0]["raw_text"] if len(exemplars) > 0 else None
            quote_2 = exemplars[1]["raw_text"] if len(exemplars) > 1 else None

            theme_id = f"theme_{cid}"
            theme = Theme(
                id=theme_id,
                cluster_id=cid,
                title=meta["title"],
                description=meta["description"],
                taxonomy_type=meta["taxonomy_type"],
                exemplar_quote_1=quote_1,
                exemplar_quote_2=quote_2,
                item_count=len(items),
                avg_severity=meta["avg_severity"],
                primary_drop_trigger=meta.get("primary_drop_trigger"),
                primary_journey_stage=meta.get("primary_journey_stage"),
                is_active=True
            )
            db.add(theme)

            # Map items
            for itm in items:
                dist = itm.get("distance_to_centroid", 0.0)
                mapping = ItemThemeMapping(
                    id=f"itm_{itm['id']}_{theme_id}",
                    feedback_id=itm["id"],
                    theme_id=theme_id,
                    distance_score=float(dist),
                    is_outlier=False
                )
                db.add(mapping)

            discovered_themes_summary.append({
                "theme_id": theme_id,
                "title": meta["title"],
                "type": meta["taxonomy_type"],
                "size": len(items),
                "severity": meta["avg_severity"],
                "quote_1": quote_1[:75] + "..." if quote_1 else "N/A",
                "quote_2": quote_2[:75] + "..." if quote_2 else "N/A",
            })

        # Record outliers if any
        for out in outliers:
            mapping = ItemThemeMapping(
                id=f"itm_{out['id']}_outlier",
                feedback_id=out["id"],
                theme_id="theme_outlier",
                distance_score=1.0,
                is_outlier=True
            )
            db.add(mapping)

    return discovered_themes_summary, len(outliers)

def run_phase4():
    logger.info("Initializing SQLite database tables...")
    init_db()

    # 1. Fetch extracted insights and join with raw text
    logger.info("Loading extracted insights from database...")
    with get_db() as db:
        insights = db.query(ExtractedInsight).all()
        insight_map = {ins.feedback_id: ins for ins in insights}

        feedback_items = (
            db.query(CleanedFeedback)
            .filter(CleanedFeedback.id.in_(insight_map.keys()))
            .all()
        )
        joined_items = []
        for fb in feedback_items:
            ins = insight_map[fb.id]
            d = fb.to_dict()
            d["journey_stage"] = ins.journey_stage
            d["drop_trigger"] = ins.drop_trigger
            d["action_taken"] = ins.action_taken
            d["severity"] = ins.severity
            d["verbatim_quote"] = ins.verbatim_quote
            joined_items.append(d)

    total_items = len(joined_items)
    logger.info(f"Loaded {total_items} items ready for semantic embeddings & clustering.")

    if total_items == 0:
        logger.warning("No extracted insights found. Please run Phase 3 first.")
        return

    # 2. Generate Dense Embeddings
    logger.info("Generating dense vector embeddings...")
    texts_to_embed = [
        f"{it['cleaned_text']} | Trigger: {it['drop_trigger']} | Stage: {it['journey_stage']}"
        for it in joined_items
    ]
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate(texts_to_embed, use_cache=False)
    logger.info(f"Embedding matrix generated: shape {embeddings.shape}")

    # 3. Perform Semantic Clustering
    logger.info("Performing unsupervised semantic clustering...")
    clusterer = SemanticClusterer(min_clusters=6, max_clusters=12)
    clustering_res = clusterer.cluster(embeddings, joined_items)

    logger.info(
        f"Clustering complete: {clustering_res['total_clusters']} clusters, "
        f"{clustering_res['outlier_count']} outliers."
    )

    # 4. Name Themes and Persist to SQLite
    logger.info("Naming themes and writing records to SQLite...")
    themes_summary, outlier_cnt = save_themes_and_mappings(clustering_res, clusterer)

    # 5. Display Comprehensive Phase 4 Summary Report
    display_phase4_report(themes_summary, outlier_cnt, total_items)

def display_phase4_report(themes_summary, outlier_cnt, total_items):
    print("\n" + "=" * 80)
    print("                 PHASE 4: SEMANTIC CLUSTERING & THEME DISCOVERY")
    print("=" * 80)

    table_data = []
    for t in sorted(themes_summary, key=lambda x: x["size"], reverse=True):
        table_data.append([
            t["theme_id"],
            t["title"],
            t["type"],
            t["size"],
            f"{t['severity']:.1f}",
            t["quote_1"]
        ])

    headers = ["Theme ID", "Discovered Theme Title", "Taxonomy", "Count", "Avg Sev", "Sample Quote"]
    print(tabulate(table_data, headers=headers, tablefmt="github"))

    print("\n[A] Clustering Synthesis:")
    print(f"  Total Relevant Items Processed : {total_items}")
    print(f"  Distinct Thematic Clusters     : {len(themes_summary)}")
    print(f"  Outliers Flagged               : {outlier_cnt}")
    print(f"  Taxonomy Breakdown             : {sum(1 for t in themes_summary if t['type']=='inductive')} Inductive (Emergent) | {sum(1 for t in themes_summary if t['type']=='deductive')} Deductive (Fixed)")

    print("-" * 80)
    print(f"Database Location: {DATABASE_PATH}")
    print("Pipeline Status  : PHASE 4 SUCCESS")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_phase4()

