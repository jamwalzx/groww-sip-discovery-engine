"""
Evaluation Metrics & Cohen's Kappa (κ) Agreement Calculator.

Computes classification accuracy, Cohen's Kappa inter-annotator agreement,
and quote integrity for structured LLM extractions against the human golden set.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
import numpy as np


def compute_accuracy(y_true: List[str], y_pred: List[str]) -> float:
    """Computes categorical accuracy percentage [0.0, 100.0]."""
    if not y_true or len(y_true) != len(y_pred):
        return 0.0
    matches = sum(1 for t, p in zip(y_true, y_pred) if str(t).strip().lower() == str(p).strip().lower())
    return round((matches / len(y_true)) * 100.0, 2)


def compute_cohens_kappa(y_true: List[str], y_pred: List[str]) -> Tuple[float, str]:
    """
    Computes Cohen's Kappa (κ) for inter-annotator / model-human agreement:
        κ = (p_o - p_e) / (1 - p_e)

    Returns (kappa_score, interpretation_band).
    Interpretation follows Landis & Koch (1977):
        < 0.00: Poor
        0.00 - 0.20: Slight
        0.21 - 0.40: Fair
        0.41 - 0.60: Moderate
        0.61 - 0.80: Substantial
        0.81 - 1.00: Near Perfect
    """
    if not y_true or len(y_true) != len(y_pred):
        return 0.0, "Invalid Inputs"

    n = len(y_true)
    y_t = [str(x).strip().lower() for x in y_true]
    y_p = [str(x).strip().lower() for x in y_pred]

    # Observed agreement (p_o)
    p_o = sum(1 for t, p in zip(y_t, y_p) if t == p) / n

    # Expected chance agreement (p_e)
    all_categories = set(y_t).union(set(y_p))
    t_counts = Counter(y_t)
    p_counts = Counter(y_p)

    p_e = sum((t_counts[cat] / n) * (p_counts[cat] / n) for cat in all_categories)

    # Edge cases
    if abs(1.0 - p_e) < 1e-9:
        kappa = 1.0 if abs(p_o - 1.0) < 1e-9 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    kappa = round(float(kappa), 2)

    # Landis & Koch interpretation band
    if kappa >= 0.81:
        band = "Near Perfect"
    elif kappa >= 0.61:
        band = "Substantial"
    elif kappa >= 0.41:
        band = "Moderate"
    elif kappa >= 0.21:
        band = "Fair"
    elif kappa >= 0.0:
        band = "Slight"
    else:
        band = "Poor"

    return kappa, band


def compute_quote_integrity(raw_texts: List[str], quotes: List[str]) -> Tuple[float, int, int]:
    """
    Verifies that every verbatim quote is an exact contiguous substring of raw_text.
    Returns (percentage, matched_count, total_count).
    """
    if not raw_texts or len(raw_texts) != len(quotes):
        return 0.0, 0, 0

    matched = 0
    for raw, q in zip(raw_texts, quotes):
        if q and raw and (q in raw):
            matched += 1

    pct = round((matched / len(raw_texts)) * 100.0, 2)
    return pct, matched, len(raw_texts)


class EvaluationHarness:
    """
    Runs systematic evaluation comparing predictions against the Golden Benchmark.
    """

    CATEGORICAL_FIELDS = [
        "journey_stage",
        "drop_trigger",
        "action_taken",
        "emotion",
        "income_stability"
    ]

    def evaluate(
        self,
        golden_items: List[Dict[str, Any]],
        predicted_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs comprehensive evaluation on all fields.
        """
        n = min(len(golden_items), len(predicted_items))
        if n == 0:
            return {"error": "Empty dataset provided"}

        g_subset = golden_items[:n]
        p_subset = predicted_items[:n]

        scorecard = {}
        for field in self.CATEGORICAL_FIELDS:
            y_true = [
                item.get(field) or item.get("segment_cues", {}).get(field, "unknown")
                for item in g_subset
            ]
            y_pred = [
                item.get(field) or item.get("segment_cues", {}).get(field, "unknown")
                for item in p_subset
            ]

            acc = compute_accuracy(y_true, y_pred)
            kappa, band = compute_cohens_kappa(y_true, y_pred)

            # Evaluation pass condition: accuracy >= 75% and kappa >= 0.65
            status = "PASS" if (acc >= 75.0 and kappa >= 0.65) else "NEEDS_REVIEW"

            scorecard[field] = {
                "accuracy_pct": acc,
                "cohens_kappa": kappa,
                "kappa_band": band,
                "status": status
            }

        # Quote Integrity Check
        raw_texts = [item.get("raw_text", "") for item in g_subset]
        quotes = [item.get("verbatim_quote", "") for item in p_subset]
        quote_pct, q_match, q_tot = compute_quote_integrity(raw_texts, quotes)
        scorecard["quote_integrity"] = {
            "accuracy_pct": quote_pct,
            "cohens_kappa": 1.0 if quote_pct == 100.0 else round(quote_pct / 100.0, 2),
            "kappa_band": "Exact Match" if quote_pct == 100.0 else "Substantial",
            "status": "PASS" if quote_pct >= 95.0 else "FAIL"
        }

        # Overall Status
        all_passed = all(sc["status"] == "PASS" for sc in scorecard.values())

        return {
            "sample_size": n,
            "overall_status": "PASS" if all_passed else "NEEDS_REVIEW",
            "fields": scorecard
        }
