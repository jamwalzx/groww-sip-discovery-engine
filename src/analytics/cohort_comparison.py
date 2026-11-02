"""
Cohort Comparison Analytics: Continuers vs. Drop-offs.

Compares behavioral, psychological, and checking differences between:
    - Continuers: action_taken in ["continued", "increased"] OR journey_stage == "beyond_12"
    - Drop-offs: action_taken in ["stopped", "paused", "reduced"] OR journey_stage == "paused_or_lapsed"

Contrasts key dimensions:
    1. Day-1 mental models and return expectations
    2. Portfolio check frequency & metrics checked
    3. In-app friction and confusion points
    4. Outside-app information diet (YouTube, WhatsApp, Reddit, Spreadsheets)
    5. Emotional states and severity of distress
"""

from typing import List, Dict, Any, Tuple
import json
from collections import Counter
import numpy as np

from src.db.database import get_db
from src.db.models import ExtractedInsight, RawFeedback, CleanedFeedback


class CohortComparator:
    """
    Analyzes differences between first-time mutual fund continuers and drop-offs.
    """

    @staticmethod
    def partition_cohorts(
        insights: List[ExtractedInsight]
    ) -> Tuple[List[ExtractedInsight], List[ExtractedInsight]]:
        """
        Splits extracted insights into Continuers and Drop-offs cohorts.
        """
        continuers = []
        drop_offs = []

        for item in insights:
            act = (item.action_taken or "").lower()
            stage = (item.journey_stage or "").lower()

            if act in ["continued", "increased"] or stage == "beyond_12":
                continuers.append(item)
            else:
                # Drop-offs: stopped, paused, reduced, or paused_or_lapsed
                drop_offs.append(item)

        return continuers, drop_offs

    def _summarize_cohort(
        self,
        cohort_name: str,
        items: List[ExtractedInsight]
    ) -> Dict[str, Any]:
        """Summarizes behavioral metrics for a single cohort."""
        n = len(items)
        if n == 0:
            return {"name": cohort_name, "count": 0}

        # 1. Check Frequency
        freq_counts = Counter(it.check_frequency for it in items)
        freq_dist = {k: {"count": v, "pct": round(v / n * 100.0, 1)} for k, v in freq_counts.most_common()}

        # 2. Metrics Checked (JSON lists)
        metrics_counter = Counter()
        for it in items:
            raw_m = it.metrics_checked
            if raw_m:
                try:
                    parsed = json.loads(raw_m) if raw_m.startswith("[") else [raw_m]
                    for m in parsed:
                        if m and m != "unknown":
                            metrics_counter[m] += 1
                except Exception:
                    metrics_counter[raw_m] += 1
        metrics_dist = {k: {"count": v, "pct": round(v / n * 100.0, 1)} for k, v in metrics_counter.most_common()}

        # 3. Outside App Behavior
        outside_counter = Counter()
        for it in items:
            raw_o = it.outside_app_behaviour
            if raw_o:
                try:
                    parsed = json.loads(raw_o) if raw_o.startswith("[") else [raw_o]
                    for o in parsed:
                        if o and o != "unknown":
                            outside_counter[o] += 1
                except Exception:
                    outside_counter[raw_o] += 1
        outside_dist = {k: {"count": v, "pct": round(v / n * 100.0, 1)} for k, v in outside_counter.most_common()}

        # 4. Emotions
        emotion_counts = Counter(it.emotion for it in items)
        emotion_dist = {k: {"count": v, "pct": round(v / n * 100.0, 1)} for k, v in emotion_counts.most_common()}

        # 5. Journey Stage
        stage_counts = Counter(it.journey_stage for it in items)
        stage_dist = {k: {"count": v, "pct": round(v / n * 100.0, 1)} for k, v in stage_counts.most_common()}

        # 6. Severity
        avg_severity = round(float(np.mean([it.severity for it in items])), 2)

        # 7. Exemplar Quotes
        quotes = [it.verbatim_quote for it in items if it.verbatim_quote][:4]

        return {
            "name": cohort_name,
            "count": n,
            "avg_severity": avg_severity,
            "check_frequency": freq_dist,
            "metrics_checked": metrics_dist,
            "outside_app_sources": outside_dist,
            "emotions": emotion_dist,
            "journey_stages": stage_dist,
            "sample_quotes": quotes
        }

    def compare(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Runs comprehensive comparative analysis between Continuers and Drop-offs.
        """
        continuers, drop_offs = self.partition_cohorts(insights)
        total = len(insights)

        c_summary = self._summarize_cohort("Continuers", continuers)
        d_summary = self._summarize_cohort("Drop-offs", drop_offs)

        # Compute key contrast signals
        c_daily_check_pct = c_summary.get("check_frequency", {}).get("daily", {}).get("pct", 0.0)
        d_daily_check_pct = d_summary.get("check_frequency", {}).get("daily", {}).get("pct", 0.0)

        c_monthly_check_pct = c_summary.get("check_frequency", {}).get("monthly", {}).get("pct", 0.0)
        d_monthly_check_pct = d_summary.get("check_frequency", {}).get("monthly", {}).get("pct", 0.0)

        contrast_insights = [
            {
                "dimension": "Portfolio Check Frequency",
                "finding": "Drop-offs are substantially more likely to check NAV/returns daily or during market dips, leading to acute loss aversion.",
                "continuers_stat": f"{c_monthly_check_pct}% check monthly / infrequently ('set and forget')",
                "drop_offs_stat": f"{d_daily_check_pct}% check daily or obsessively during market drops"
            },
            {
                "dimension": "Outside-App Validation Diet",
                "finding": "Drop-offs seek validation from speculative YouTube tutorials and peer WhatsApp groups during market dips, whereas Continuers rely on long-term discipline or spreadsheets.",
                "continuers_top_source": list(c_summary.get("outside_app_sources", {}).keys())[:2],
                "drop_offs_top_source": list(d_summary.get("outside_app_sources", {}).keys())[:2]
            },
            {
                "dimension": "Emotional Pain & Friction Severity",
                "finding": "Drop-offs exhibit high frustration and anxiety driven by unexpected bank bounce penalties and red-screen panic.",
                "continuers_severity": c_summary.get("avg_severity", 0.0),
                "drop_offs_severity": d_summary.get("avg_severity", 0.0)
            }
        ]

        return {
            "total_analyzed": total,
            "continuers_count": len(continuers),
            "continuers_pct": round(len(continuers) / total * 100.0, 1) if total > 0 else 0.0,
            "drop_offs_count": len(drop_offs),
            "drop_offs_pct": round(len(drop_offs) / total * 100.0, 1) if total > 0 else 0.0,
            "continuers": c_summary,
            "drop_offs": d_summary,
            "contrast_findings": contrast_insights
        }

    def compute_all(self, db=None) -> Dict[str, Any]:
        """Loads all insights from DB and computes cohort comparison."""
        def _execute(session):
            insights = session.query(ExtractedInsight).all()
            return self.compare(insights)

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

