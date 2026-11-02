"""
Segment Analytics for First-Time Mutual Fund SIP Continuation.

Computes cross-tabulations of drop triggers, friction themes, and actions taken
across demographic and behavioral segments:
    - income_stability (salaried_stable, gig_freelance, student_dependent, irregular_business, unknown)
    - age_band (<22, 22-28, 29-35, 36+, unknown)
    - influencer (self, friend_colleague, family, youtuber_finfluencer, advisor, app_nudge, unknown)
    - source_of_money (salary, pocket_money, savings, windfall, unknown)
    - investor_experience (first_time, intermediate, experienced, unknown)

Statistical Rigor Safeguard:
    Enforces n < 30 threshold flagging. Any cohort with n < 30 has:
        low_confidence = True
        confidence_status = "⚠️ Low Confidence (n={n} < 30): Small sample size; interpret directionally, not definitively."
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np

from src.db.database import get_db
from src.db.models import ExtractedInsight, Theme, ItemThemeMapping


SAMPLE_SIZE_THRESHOLD = 30


class SegmentAnalyzer:
    """
    Performs multi-dimensional segment cross-tabulations with strict sample-size safeguards.
    """

    def __init__(self, sample_size_threshold: int = SAMPLE_SIZE_THRESHOLD):
        self.sample_size_threshold = sample_size_threshold

    def get_confidence_metadata(self, count: int) -> Dict[str, Any]:
        """Returns statistical confidence metadata based on sample size."""
        is_low = count < self.sample_size_threshold
        if is_low:
            message = (
                f"⚠️ Low Confidence (n={count} < {self.sample_size_threshold}): "
                "Small sample size; interpret directionally, not definitively."
            )
            badge = "LOW_CONFIDENCE"
        else:
            message = f"✅ High Confidence (n={count} >= {self.sample_size_threshold}): Statistically robust."
            badge = "HIGH_CONFIDENCE"

        return {
            "n": count,
            "low_confidence": is_low,
            "confidence_status": message,
            "badge": badge,
            "threshold": self.sample_size_threshold
        }

    def analyze_dimension(
        self,
        insights: List[ExtractedInsight],
        dimension_attr: str,
        dimension_label: str
    ) -> Dict[str, Any]:
        """
        Groups insights by a demographic/segment dimension attribute and calculates:
        - Total sample count and confidence metadata
        - Drop trigger distributions
        - Action taken distributions
        - Average severity
        - Top emotion distributions
        """
        grouped: Dict[str, List[ExtractedInsight]] = {}
        for ins in insights:
            val = getattr(ins, dimension_attr, "unknown") or "unknown"
            grouped.setdefault(val, []).append(ins)

        cohorts_report = {}
        for seg_val, seg_items in grouped.items():
            n = len(seg_items)
            conf = self.get_confidence_metadata(n)

            # Drop trigger distribution
            drop_counts = Counter(item.drop_trigger for item in seg_items)
            drop_dist = {
                trig: {"count": cnt, "pct": round(cnt / n * 100.0, 1)}
                for trig, cnt in drop_counts.most_common()
            }

            # Action taken distribution
            action_counts = Counter(item.action_taken for item in seg_items)
            action_dist = {
                act: {"count": cnt, "pct": round(cnt / n * 100.0, 1)}
                for act, cnt in action_counts.most_common()
            }

            # Emotion distribution
            emotion_counts = Counter(item.emotion for item in seg_items)
            emotion_dist = {
                emo: {"count": cnt, "pct": round(cnt / n * 100.0, 1)}
                for emo, cnt in emotion_counts.most_common()
            }

            # Mean severity
            avg_severity = round(float(np.mean([item.severity for item in seg_items])), 2)

            cohorts_report[seg_val] = {
                "segment_value": seg_val,
                "sample_size": n,
                "confidence": conf,
                "avg_severity": avg_severity,
                "drop_triggers": drop_dist,
                "top_drop_trigger": drop_counts.most_common(1)[0][0] if drop_counts else "unknown",
                "actions_taken": action_dist,
                "continuer_rate_pct": round(
                    sum(1 for it in seg_items if it.action_taken in ["continued", "increased"]) / n * 100.0, 1
                ),
                "drop_off_rate_pct": round(
                    sum(1 for it in seg_items if it.action_taken in ["stopped", "paused", "reduced"]) / n * 100.0, 1
                ),
                "emotions": emotion_dist,
                "sample_verbatim_quotes": [
                    it.verbatim_quote for it in seg_items if it.verbatim_quote
                ][:3]
            }

        return {
            "dimension": dimension_attr,
            "label": dimension_label,
            "total_items": len(insights),
            "cohort_count": len(grouped),
            "cohorts": cohorts_report
        }

    def compute_all_segments(self, db=None) -> Dict[str, Any]:
        """
        Loads all insights from DB and computes cross-tabulations across all standard dimensions.
        """
        def _execute(session):
            insights = session.query(ExtractedInsight).all()
            if not insights:
                return {}

            total_n = len(insights)
            overall_conf = self.get_confidence_metadata(total_n)

            dimensions = [
                ("income_stability", "Income Stability"),
                ("age_band", "Age Band"),
                ("influencer", "Primary Influencer"),
                ("source_of_money", "Source of Funds"),
                ("investor_experience", "Investor Experience Level"),
            ]

            reports = {}
            for attr, label in dimensions:
                reports[attr] = self.analyze_dimension(insights, attr, label)

            return {
                "total_insights_analyzed": total_n,
                "overall_confidence": overall_conf,
                "dimensions": reports
            }

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

