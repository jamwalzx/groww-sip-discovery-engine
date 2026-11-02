"""
Unit tests for Phase 6: Human-in-the-Loop Golden Set & Evaluation Harness.
"""

import pytest
import tempfile
import os

from src.evals.golden_set import (
    get_golden_benchmark,
    export_golden_set_csv,
    load_golden_set_csv
)
from src.evals.metrics import (
    compute_accuracy,
    compute_cohens_kappa,
    compute_quote_integrity,
    EvaluationHarness
)
from src.evals.failure_taxonomy import FailureTaxonomyClassifier
from src.evals.audit_log import AuditLogManager
from src.evals.bias_panel import SourceBiasAuditor


def test_cohens_kappa_calculation():
    """Verify Cohen's Kappa math under known distributions."""
    # 1. Perfect agreement
    y1 = ["month_1_3", "month_4_12", "beyond_12", "month_1_3"]
    y2 = ["month_1_3", "month_4_12", "beyond_12", "month_1_3"]
    k_perf, band_perf = compute_cohens_kappa(y1, y2)
    assert k_perf == 1.0
    assert band_perf == "Near Perfect"

    # 2. Complete disagreement
    y_true = ["a", "a", "a", "a"]
    y_pred = ["b", "b", "b", "b"]
    k_zero, band_zero = compute_cohens_kappa(y_true, y_pred)
    assert k_zero <= 0.0

    # 3. Substantial agreement
    yt = ["cat", "dog", "cat", "dog", "cat", "dog", "cat", "dog", "cat", "dog"]
    yp = ["cat", "dog", "cat", "dog", "cat", "dog", "cat", "dog", "dog", "cat"]
    k_sub, band_sub = compute_cohens_kappa(yt, yp)
    assert k_sub >= 0.60


def test_quote_integrity_metric():
    """Verify quote integrity computation."""
    raws = [
        "Bank charged 500 penalty fee.",
        "Market fell and I panicked.",
        "NAV delayed by 2 days."
    ]
    # Perfect quotes
    quotes_valid = [
        "500 penalty fee",
        "Market fell",
        "NAV delayed by 2 days."
    ]
    pct, matched, total = compute_quote_integrity(raws, quotes_valid)
    assert pct == 100.0
    assert matched == 3
    assert total == 3

    # Corrupted quote
    quotes_corrupted = [
        "500 penalty fee",
        "I was crying and screaming",  # Hallucinated
        "NAV delayed"
    ]
    pct2, matched2, total2 = compute_quote_integrity(raws, quotes_corrupted)
    assert abs(pct2 - 66.67) < 0.1
    assert matched2 == 2


def test_golden_set_structure_and_export():
    """Verify that golden dataset contains 25 valid items and exports cleanly to CSV."""
    items = get_golden_benchmark()
    assert len(items) == 25

    for it in items:
        assert "id" in it
        assert "raw_text" in it
        assert "drop_trigger" in it
        assert "action_taken" in it
        assert "verbatim_quote" in it
        assert it["verbatim_quote"] in it["raw_text"], f"Quote mismatch in {it['id']}"

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        exported_path = export_golden_set_csv(tmp_path)
        assert os.path.exists(exported_path)
        loaded = load_golden_set_csv(exported_path)
        assert len(loaded) == 25
        assert loaded[0]["id"] == "gold_01"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_failure_taxonomy_classification():
    """Verify classification of prediction discrepancies into failure taxonomy."""
    classifier = FailureTaxonomyClassifier()

    # Sarcasm case
    sarcasm_item = {
        "id": "t1",
        "raw_text": "Great app, charged me 350 rs bounce penalty! Best investment platform ever!",
        "failure_challenge": "sarcasm_irony"
    }
    mode = classifier.classify_error(sarcasm_item, {"action_taken": "none"})
    assert mode == "sarcasm_irony"

    # Hinglish case
    hinglish_item = {
        "id": "t2",
        "raw_text": "Paisa kat gaya bank se par portfolio me nahi dikha. Paused it for now.",
        "failure_challenge": "hinglish_ambiguity"
    }
    mode_hi = classifier.classify_error(hinglish_item, {"drop_trigger": "unknown"})
    assert mode_hi == "hinglish_ambiguity"


def test_audit_log_manager():
    """Verify audit log records human corrections and validates mandatory justifications."""
    mgr = AuditLogManager()
    seeded = mgr.seed_default_cases()
    assert seeded >= 0

    all_cases = mgr.get_all_corrections()
    assert len(all_cases) >= 3

    # Test adding a valid correction
    new_corr = mgr.add_correction(
        feedback_id="test_fb_123",
        field_corrected="emotion",
        original_value="anxious",
        corrected_value="frustrated",
        justification_reason="Reviewer confirmed tone was angry regarding bank debit failure, not anxious.",
        reviewer_id="pm_reviewer_test",
        failure_mode="multi_topic_complexity"
    )
    assert new_corr["field_corrected"] == "emotion"
    assert new_corr["corrected_value"] == "frustrated"

    # Test rejection of missing/short justification reason
    with pytest.raises(ValueError, match="mandatory and must be at least 10 characters"):
        mgr.add_correction(
            feedback_id="test_fb_invalid",
            field_corrected="emotion",
            original_value="anxious",
            corrected_value="frustrated",
            justification_reason="bad"  # < 10 chars
        )


def test_bias_panel_auditor():
    """Verify source bias auditor aggregates platform metrics."""
    auditor = SourceBiasAuditor()
    report = auditor.audit()

    assert "total_raw_volume" in report
    assert "platforms" in report
    assert "play_store" in report["platforms"]
    assert report["platforms"]["play_store"]["channel_name"] == "Google Play Store Reviews"
    assert "inherent_bias" in report["platforms"]["play_store"]

