"""
Phase 5 Analytics Runner: Opportunity Matrix, Segmentation, and Cohorts.

Executes the quantitative Opportunity Scoring algorithm, segment cross-tabulations
with sample size safeguards (n < 30), continuer vs. drop-off comparative analysis,
and core product question (Q1-Q9) syntheses.

Usage:
    .venv\\Scripts\\python.exe -m scripts.run_phase5_analytics
"""

import sys
from datetime import datetime, timezone
from tabulate import tabulate

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.db.database import get_db, init_db
from src.db.models import Theme, ExtractedInsight, OpportunityScoreRecord
from src.analytics.opportunity_matrix import OpportunityMatrixCalculator
from src.analytics.segmentation import SegmentAnalyzer
from src.analytics.cohort_comparison import CohortComparator
from src.analytics.question_views import QuestionViewAggregator


def run_phase5():
    print("=" * 90)
    print("  AI DISCOVERY ENGINE — PHASE 5: OPPORTUNITY MATRIX & SEGMENT ANALYTICS")
    print("=" * 90)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # 1. Initialize tables if needed
    init_db()

    # 2. Opportunity Matrix Formulation
    print("\n[Step 1/4] Computing Multi-Factor Opportunity Matrix for Discovered Themes...")
    opp_calc = OpportunityMatrixCalculator(
        weight_frequency=0.30,
        weight_severity=0.30,
        weight_proximity=0.40
    )
    scored_themes = opp_calc.compute_all()
    if not scored_themes:
        print("❌ Error: No themes found in database. Please run Phase 4 clustering first.")
        return

    # Persist to SQLite
    saved_count = opp_calc.save_to_db(scored_themes)
    print(f"  ✓ Calculated scores for {len(scored_themes)} themes ({saved_count} records saved to 'opportunity_scores' table)")

    # Print Ranked Opportunity Matrix Table
    print("\n" + "=" * 90)
    print("  RANKED OPPORTUNITY MATRIX (Impact vs. Addressability)")
    print("  Impact = (0.30 * F_norm + 0.30 * S_norm + 0.40 * P_norm) * 100")
    print("  Opportunity Score = Impact * A_norm (Scaled 0 - 100)")
    print("=" * 90)

    matrix_rows = []
    for item in scored_themes:
        matrix_rows.append([
            item["rank"],
            (item["theme_title"][:42] + "..") if len(item["theme_title"]) > 44 else item["theme_title"],
            item["taxonomy_type"],
            f"{item['frequency_pct']:.1f}%",
            f"{item['severity_score']:.1f}",
            f"{item['proximity_score']:.1f}",
            f"{item['addressability_score']:.1f}",
            f"{item['impact_score']:.1f}",
            f"{item['opportunity_score']:.1f} / 100"
        ])

    headers = ["Rank", "Theme Title", "Taxonomy", "Freq%", "Sev", "Prox", "Addr", "Impact", "Opp Score"]
    print(tabulate(matrix_rows, headers=headers, tablefmt="github"))

    # Top 3 Strategic Recommendations adhering strictly to compliance constraints
    print("\n--- TOP 3 STRATEGIC PRODUCT RECOMMENDATIONS ---")
    for item in scored_themes[:3]:
        print(f"\n🏆 Rank #{item['rank']}: {item['theme_title']}")
        print(f"   • Opportunity Score: {item['opportunity_score']:.1f} / 100 (Impact: {item['impact_score']:.1f}, Addr: {item['addressability_score']:.1f}/5)")
        print(f"   • Strategic Intervention: {item['strategic_rationale']}")
        print(f"   • Compliance Guardrail: {item['addressability_feasibility']}")
        print(f"   • Evidence Quote: \"{item['exemplar_quote'][:90]}...\"")

    # 3. Segment Analytics with Sample Size Safeguards (n < 30)
    print("\n" + "=" * 90)
    print("  [Step 2/4] Segment Analytics & Sample-Size Rigor Safeguards (n < 30)")
    print("=" * 90)
    segment_analyzer = SegmentAnalyzer()
    seg_results = segment_analyzer.compute_all_segments()

    for dim_key, dim_report in seg_results.get("dimensions", {}).items():
        print(f"\n📊 Dimension: {dim_report['label']} (Total: {dim_report['total_items']} items across {dim_report['cohort_count']} cohorts)")
        seg_rows = []
        for cohort_val, cdata in dim_report["cohorts"].items():
            conf_badge = "⚠️ LOW (n<30)" if cdata["confidence"]["low_confidence"] else "✅ HIGH (n>=30)"
            seg_rows.append([
                cohort_val,
                cdata["sample_size"],
                conf_badge,
                f"{cdata['avg_severity']:.1f}",
                cdata["top_drop_trigger"],
                f"{cdata['drop_off_rate_pct']:.1f}%",
                f"{cdata['continuer_rate_pct']:.1f}%"
            ])
        print(tabulate(
            seg_rows,
            headers=["Cohort / Value", "Sample (n)", "Confidence Badge", "Avg Sev", "Top Drop Trigger", "Drop-off %", "Continuer %"],
            tablefmt="github"
        ))

    # 4. Continuers vs. Drop-offs Cohort Analytics
    print("\n" + "=" * 90)
    print("  [Step 3/4] Continuers vs. Drop-offs Comparative Cohort Analytics")
    print("=" * 90)
    comparator = CohortComparator()
    cohort_report = comparator.compute_all()

    print(f"Total Feedback Analyzed: {cohort_report['total_analyzed']}")
    print(f"  • Disciplined Continuers: {cohort_report['continuers_count']} ({cohort_report['continuers_pct']}%)")
    print(f"  • Churned / Paused Drop-offs: {cohort_report['drop_offs_count']} ({cohort_report['drop_offs_pct']}%)")

    contrast_rows = []
    for c in cohort_report.get("contrast_findings", []):
        contrast_rows.append([
            c["dimension"],
            c["continuers_stat"] if "continuers_stat" in c else str(c.get("continuers_severity") or c.get("continuers_top_source")),
            c["drop_offs_stat"] if "drop_offs_stat" in c else str(c.get("drop_offs_severity") or c.get("drop_offs_top_source")),
            c["finding"]
        ])
    print("\n" + tabulate(contrast_rows, headers=["Dimension", "Continuers Cohort", "Drop-offs Cohort", "Behavioral Contrast Finding"], tablefmt="github"))

    # 5. Core Questions Q1-Q9 Summary View
    print("\n" + "=" * 90)
    print("  [Step 4/4] Behavioral Core Question Views (Q1 to Q9) Pre-Aggregation")
    print("=" * 90)
    q_aggregator = QuestionViewAggregator()
    all_q = q_aggregator.get_all_questions()

    for q_id in ["Q1", "Q3", "Q4", "Q5", "Q9"]:
        q_data = all_q.get(q_id, {})
        print(f"\n📌 {q_data.get('question_id')}: {q_data.get('question_title')}")
        print(f"   Takeaway: {q_data.get('key_takeaway')}")
        quotes = q_data.get("quote_cards", [])
        if quotes:
            print(f"   Verified Quote [1/{len(quotes)}]: \"{quotes[0]['verbatim_quote'][:80]}...\" (Verified: {quotes[0]['is_verified']})")

    print("\n" + "=" * 90)
    print("  PHASE 5 VERIFICATION COMPLETED SUCCESSFULLY")
    print("=" * 90)


if __name__ == "__main__":
    run_phase5()

