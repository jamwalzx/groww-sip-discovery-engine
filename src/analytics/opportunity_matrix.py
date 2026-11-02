"""
Opportunity Matrix Calculator for First-Time Mutual Fund SIP Continuation.

Computes a multi-factor Opportunity Score for each discovered behavioral theme:
    Impact = (w_f * F_norm + w_s * S_norm + w_p * P_norm) * 100
    Opportunity Score = Impact * A_norm

Where:
    - Frequency (F): Relative prevalence of the theme (% of relevant feedback)
    - Severity (S): Average user pain/distress (1.0 - 5.0)
    - Proximity to Continuation (P): Direct empirical or rubric link to SIP drop-off (1.0 - 5.0)
    - Addressability (A): Feasibility of product intervention satisfying constraints (1.0 - 5.0)
        * Strictly no fear/FOMO/urgency triggers
        * Strictly no stock or mutual fund picking / direct financial advisory

Default weights: w_f = 0.30, w_s = 0.30, w_p = 0.40 (sum = 1.0).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np

from src.db.database import get_db
from src.db.models import Theme, ExtractedInsight, ItemThemeMapping, OpportunityScoreRecord


# Standard Product Addressability Knowledge Base adhering strictly to compliance constraints
THEME_ADDRESSABILITY_RUBRIC = {
    "autopay": {
        "score": 4.8,
        "rationale": "High feasibility: Flexible SIP debit date picker (post-salary buffer), proactive debit WhatsApp/SMS reminders 24h prior, automated retry without bank penalty, instant 1-click pause.",
        "compliance_notes": "Pure transactional UX; zero fund advisory or urgency manipulation."
    },
    "nav_delay": {
        "score": 4.4,
        "rationale": "High feasibility: In-app transparent NAV allocation visualizer, live timeline ('Order placed -> AMC confirmed -> Units allotted by 9 PM'), reducing support anxiety.",
        "compliance_notes": "Factual status transparency; zero market prediction."
    },
    "negative_returns": {
        "score": 4.0,
        "rationale": "Medium-High feasibility: Volatility framing UI, Rupee-Cost Averaging explainers, long-term horizon toggle, suppression of daily red-day alarms for SIP portfolios.",
        "compliance_notes": "Educational behavioral nudges; strictly avoids stock/fund selection or return guarantees."
    },
    "customer_support": {
        "score": 3.8,
        "rationale": "Medium feasibility: Dedicated SIP self-service resolver, direct NPCI mandate status lookup, automatic ticket dispatch for failed debits.",
        "compliance_notes": "Operational service improvement; fully compliant."
    },
    "cash_crunch": {
        "score": 3.6,
        "rationale": "Medium feasibility: 'Smart Pause' (skip 1-3 instalments without mandate cancellation), temporary SIP amount step-down.",
        "compliance_notes": "Empowers user financial flexibility without penalty nudges."
    },
    "continuers": {
        "score": 3.4,
        "rationale": "Medium feasibility: Annual milestone celebrations, compounding milestone charts, auto step-up on appraisal month.",
        "compliance_notes": "Affirmative positive reinforcement for disciplined investing."
    },
    "general": {
        "score": 3.5,
        "rationale": "Medium feasibility: Streamlined SIP management screen, clear active vs paused filters.",
        "compliance_notes": "Standard product UI improvement."
    }
}


def get_addressability_for_theme(title: str, description: str = "") -> Dict[str, Any]:
    """
    Matches a theme title/description to its addressability feasibility score and rationale,
    ensuring strict compliance with Groww product guardrails.
    """
    title_lower = title.lower()
    text = (title + " " + description).lower()

    # Prioritize specific thematic intents:
    # 1. Disciplined Continuers
    if any(k in title_lower for k in ["continuer", "disciplined", "habit", "multi-year"]):
        return THEME_ADDRESSABILITY_RUBRIC["continuers"]
    # 2. Customer Support Lag
    elif any(k in title_lower for k in ["support", "ticket", "resolution lag", "customer care"]):
        return THEME_ADDRESSABILITY_RUBRIC["customer_support"]
    # 3. NAV Cut-off & Settlement Latency
    elif any(k in title_lower for k in ["nav", "cut-off", "settlement", "allotment", "delay"]):
        return THEME_ADDRESSABILITY_RUBRIC["nav_delay"]
    # 4. Negative Returns & Volatility Panic
    elif any(k in title_lower for k in ["negative", "return", "xirr", "volatility", "panic", "disappointment", "red"]):
        return THEME_ADDRESSABILITY_RUBRIC["negative_returns"]
    # 5. Autopay / Salary Date Mismatch / Bounce Fees
    elif any(k in text for k in ["salary date", "autopay", "mandate", "bounce", "bank charges", "debit rejection"]):
        return THEME_ADDRESSABILITY_RUBRIC["autopay"]
    # 6. Cash Crunch / Irregular Income
    elif any(k in text for k in ["cash crunch", "irregular", "student", "afford"]):
        return THEME_ADDRESSABILITY_RUBRIC["cash_crunch"]
    else:
        return THEME_ADDRESSABILITY_RUBRIC["general"]


def normalize_value(val: float, min_val: float, max_val: float) -> float:
    """Normalizes a float value to the [0.0, 1.0] range safely."""
    if max_val <= min_val:
        return 1.0 if val >= min_val else 0.0
    return float(np.clip((val - min_val) / (max_val - min_val), 0.0, 1.0))


class OpportunityMatrixCalculator:
    """
    Computes quantified Opportunity Scores and coordinates the Opportunity Matrix.
    """

    def __init__(
        self,
        weight_frequency: float = 0.30,
        weight_severity: float = 0.30,
        weight_proximity: float = 0.40
    ):
        # Validate weights sum close to 1.0
        total_w = weight_frequency + weight_severity + weight_proximity
        if total_w <= 0:
            weight_frequency, weight_severity, weight_proximity = 0.30, 0.30, 0.40
            total_w = 1.0
        self.w_f = weight_frequency / total_w
        self.w_s = weight_severity / total_w
        self.w_p = weight_proximity / total_w

    def set_weights(self, w_f: float, w_s: float, w_p: float):
        """Update scoring weights dynamically."""
        total = w_f + w_s + w_p
        if total > 0:
            self.w_f = w_f / total
            self.w_s = w_s / total
            self.w_p = w_p / total

    def compute_proximity(
        self,
        theme_title: str,
        mapped_insights: List[ExtractedInsight]
    ) -> float:
        """
        Computes the Proximity to Continuation (1.0 to 5.0).
        Measures the directness of the theme in causing SIP stoppage, pausing, or lapsing.
        Combines domain rubric baseline with empirical evidence from mapped feedback.
        """
        title_lower = theme_title.lower()

        # Domain rubric baseline for proximity to drop-off
        if any(k in title_lower for k in ["continuer", "disciplined", "habit", "multi-year"]):
            rubric_p = 1.2
        elif any(k in title_lower for k in ["salary", "autopay", "mandate", "bounce", "debit rejection"]):
            rubric_p = 4.8
        elif any(k in title_lower for k in ["negative", "return", "xirr", "panic", "disappointment", "volatility"]):
            rubric_p = 4.5
        elif any(k in title_lower for k in ["cash", "crunch", "irregular", "afford"]):
            rubric_p = 4.4
        elif any(k in title_lower for k in ["nav", "cut-off", "settlement", "delay", "allotment"]):
            rubric_p = 3.2
        elif any(k in title_lower for k in ["support", "resolution", "ticket"]):
            rubric_p = 3.0
        else:
            rubric_p = 2.5

        if not mapped_insights:
            return round(rubric_p, 2)

        # Empirical drop rate from mapped insights
        drop_actions = {"stopped", "paused", "reduced", "switched_fund", "switched_platform"}
        critical_triggers = {
            "payment_failure", "cash_crunch", "income_irregularity",
            "market_drop", "underwhelming_returns", "confusion"
        }

        drop_count = sum(1 for ins in mapped_insights if ins.action_taken in drop_actions)
        trigger_count = sum(1 for ins in mapped_insights if ins.drop_trigger in critical_triggers)
        n = len(mapped_insights)

        drop_rate = drop_count / n
        trigger_rate = trigger_count / n

        # Blended empirical proximity [1.0, 5.0]
        empirical_p = 1.0 + 4.0 * (0.60 * drop_rate + 0.40 * trigger_rate)

        # Blend: 50% domain baseline, 50% empirical observation
        blended_p = 0.50 * rubric_p + 0.50 * empirical_p
        return round(float(np.clip(blended_p, 1.0, 5.0)), 2)

    def calculate_theme_opportunity(
        self,
        theme: Theme,
        total_feedback_count: int,
        max_theme_count: int,
        mapped_insights: List[ExtractedInsight]
    ) -> Dict[str, Any]:
        """
        Computes the complete Opportunity Matrix record for a single Theme.
        """
        item_count = len(mapped_insights) if mapped_insights else (theme.item_count or 0)
        
        # 1. Frequency (F)
        freq_pct = (item_count / total_feedback_count * 100.0) if total_feedback_count > 0 else 0.0
        # Normalize relative to the largest theme count
        f_norm = (item_count / max_theme_count) if max_theme_count > 0 else 0.0
        f_norm = float(np.clip(f_norm, 0.0, 1.0))

        # 2. Severity (S)
        if mapped_insights:
            s_raw = float(np.mean([ins.severity for ins in mapped_insights]))
        else:
            s_raw = float(theme.avg_severity) if theme.avg_severity else 2.5
        s_norm = normalize_value(s_raw, 1.0, 5.0)

        # 3. Proximity (P)
        p_raw = self.compute_proximity(theme.title, mapped_insights)
        p_norm = normalize_value(p_raw, 1.0, 5.0)

        # 4. Addressability (A)
        addr_info = get_addressability_for_theme(theme.title, theme.description)
        a_raw = float(addr_info["score"])
        a_norm = normalize_value(a_raw, 1.0, 5.0)

        # 5. Impact = (w_f * F_norm + w_s * S_norm + w_p * P_norm) * 100
        impact = (self.w_f * f_norm + self.w_s * s_norm + self.w_p * p_norm) * 100.0
        impact = float(np.clip(impact, 0.0, 100.0))

        # 6. Opportunity Score = Impact * A_norm
        opp_score = impact * a_norm
        opp_score = float(np.clip(opp_score, 0.0, 100.0))

        # 7. Exemplar quote selection
        exemplar = theme.exemplar_quote_1
        if not exemplar and mapped_insights:
            exemplar = mapped_insights[0].verbatim_quote

        # 8. Trend velocity (relative split over time if timestamps exist)
        trend_velocity = 0.0
        if len(mapped_insights) >= 2:
            dates = [ins.created_at for ins in mapped_insights if ins.created_at]
            if len(dates) >= 2:
                mid = len(dates) // 2
                recent_half = len(dates) - mid
                older_half = mid
                if older_half > 0:
                    trend_velocity = round((recent_half - older_half) / older_half, 2)

        return {
            "theme_id": theme.id,
            "theme_title": theme.title,
            "taxonomy_type": theme.taxonomy_type,
            "item_count": item_count,
            "frequency_pct": round(freq_pct, 2),
            "frequency_norm": round(f_norm, 3),
            "severity_score": round(s_raw, 2),
            "severity_norm": round(s_norm, 3),
            "proximity_score": round(p_raw, 2),
            "proximity_norm": round(p_norm, 3),
            "addressability_score": round(a_raw, 2),
            "addressability_norm": round(a_norm, 3),
            "impact_score": round(impact, 1),
            "opportunity_score": round(opp_score, 1),
            "trend_velocity": trend_velocity,
            "primary_drop_trigger": theme.primary_drop_trigger or "unknown",
            "exemplar_quote": exemplar,
            "strategic_rationale": addr_info["rationale"],
            "addressability_feasibility": addr_info["compliance_notes"]
        }

    def compute_all(self, db=None) -> List[Dict[str, Any]]:
        """
        Loads all themes and mappings from SQLite, computes opportunity scores,
        ranks them descending by opportunity score, and returns list of dictionaries.
        """
        def _execute(session):
            themes = session.query(Theme).filter(Theme.is_active == True).all()
            if not themes:
                return []

            # Preload all insights and mappings for performance
            mappings = session.query(ItemThemeMapping).all()
            insights = {ins.id: ins for ins in session.query(ExtractedInsight).all()}

            theme_insights_map = {t.id: [] for t in themes}
            for m in mappings:
                if m.theme_id in theme_insights_map:
                    # m.feedback_id can be 'ins_...' or raw id
                    ins = insights.get(m.feedback_id) or insights.get(f"ins_{m.feedback_id}")
                    if ins:
                        theme_insights_map[m.theme_id].append(ins)

            total_feedback = sum(len(items) for items in theme_insights_map.values())
            if total_feedback == 0:
                total_feedback = sum(t.item_count for t in themes) or 1

            max_count = max([len(items) for items in theme_insights_map.values()] + [t.item_count for t in themes] + [1])

            scored_themes = []
            for t in themes:
                t_insights = theme_insights_map.get(t.id, [])
                score_dict = self.calculate_theme_opportunity(t, total_feedback, max_count, t_insights)
                scored_themes.append(score_dict)

            # Sort descending by opportunity_score, secondary sort by impact_score
            scored_themes.sort(key=lambda x: (x["opportunity_score"], x["impact_score"]), reverse=True)

            # Assign ranks
            for rank_idx, record in enumerate(scored_themes, start=1):
                record["rank"] = rank_idx

            return scored_themes

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

    def save_to_db(self, scored_themes: List[Dict[str, Any]], db=None) -> int:
        """
        Persists ranked Opportunity Score records to SQLite `opportunity_scores` table.
        """
        def _execute(session):
            saved = 0
            for item in scored_themes:
                rec_id = f"opp_{item['theme_id']}"
                existing = session.query(OpportunityScoreRecord).filter_by(id=rec_id).first()
                if not existing:
                    existing = OpportunityScoreRecord(id=rec_id, theme_id=item["theme_id"])
                    session.add(existing)

                existing.theme_title = item["theme_title"]
                existing.taxonomy_type = item["taxonomy_type"]
                existing.item_count = item["item_count"]
                existing.frequency_pct = item["frequency_pct"]
                existing.frequency_norm = item["frequency_norm"]
                existing.severity_score = item["severity_score"]
                existing.severity_norm = item["severity_norm"]
                existing.proximity_score = item["proximity_score"]
                existing.proximity_norm = item["proximity_norm"]
                existing.addressability_score = item["addressability_score"]
                existing.addressability_norm = item["addressability_norm"]
                existing.impact_score = item["impact_score"]
                existing.opportunity_score = item["opportunity_score"]
                existing.trend_velocity = item["trend_velocity"]
                existing.rank = item["rank"]
                existing.primary_drop_trigger = item["primary_drop_trigger"]
                existing.exemplar_quote = item["exemplar_quote"]
                existing.strategic_rationale = item["strategic_rationale"]
                existing.addressability_feasibility = item["addressability_feasibility"]
                existing.updated_at = datetime.now(timezone.utc)
                saved += 1
            return saved

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)
