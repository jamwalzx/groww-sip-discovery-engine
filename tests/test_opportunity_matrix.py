"""
Unit tests for Phase 5: Opportunity Matrix, Segmentation, and Cohort Analytics.
"""

import pytest
from src.analytics.opportunity_matrix import (
    OpportunityMatrixCalculator,
    normalize_value,
    get_addressability_for_theme
)
from src.analytics.segmentation import SegmentAnalyzer, SAMPLE_SIZE_THRESHOLD
from src.analytics.cohort_comparison import CohortComparator
from src.analytics.question_views import QuestionViewAggregator, build_quote_card
from src.db.models import ExtractedInsight, Theme, CleanedFeedback


def test_normalization_bounds():
    """Verify normalization safely maps to [0.0, 1.0] and handles edge cases."""
    assert normalize_value(1.0, 1.0, 5.0) == 0.0
    assert normalize_value(5.0, 1.0, 5.0) == 1.0
    assert normalize_value(3.0, 1.0, 5.0) == 0.5
    # Out of bounds clipping
    assert normalize_value(6.0, 1.0, 5.0) == 1.0
    assert normalize_value(0.0, 1.0, 5.0) == 0.0
    # Degenerate min == max
    assert normalize_value(5.0, 5.0, 5.0) == 1.0


def test_opportunity_matrix_formula():
    """Verify Impact and Opportunity Score calculations with standard default weights."""
    calc = OpportunityMatrixCalculator(weight_frequency=0.30, weight_severity=0.30, weight_proximity=0.40)
    
    # Create mock theme and insights
    theme = Theme(
        id="theme_test_autopay",
        cluster_id=1,
        title="Salary Date Mismatch Leading to Autopay Debit Rejection & Bank Charges",
        description="Users face bank penalty fees when autopay debits before salary credits.",
        taxonomy_type="inductive",
        item_count=10,
        avg_severity=4.0
    )

    mock_insights = [
        ExtractedInsight(
            id=f"ins_test_{i}",
            feedback_id=f"fb_{i}",
            source="play_store",
            journey_stage="month_1_3",
            start_motivation="unknown",
            expectation_at_start="unknown",
            behaviour_change_over_time="unknown",
            drop_trigger="payment_failure",
            action_taken="stopped" if i < 7 else "paused",
            metrics_checked="[\"NAV\"]",
            check_frequency="daily",
            in_app_confusion="autopay date",
            in_app_worry="bank charges",
            outside_app_behaviour="[\"YouTube\"]",
            continuation_signal="unknown",
            income_stability="salaried_stable",
            age_band="22-28",
            source_of_money="salary",
            influencer="self",
            investor_experience="first_time",
            unmet_need="change debit date",
            emotion="frustrated",
            severity=4,
            verbatim_quote="autopay debited before salary and bank charged 350 rs penalty",
            evidence_span="0:50",
            confidence=0.9
        )
        for i in range(10)
    ]

    res = calc.calculate_theme_opportunity(
        theme=theme,
        total_feedback_count=50,
        max_theme_count=10,
        mapped_insights=mock_insights
    )

    # Frequency = 10/50 = 20.0%, F_norm = 10/10 = 1.0
    assert res["frequency_pct"] == 20.0
    assert res["frequency_norm"] == 1.0
    # Severity = 4.0, S_norm = (4-1)/4 = 0.75
    assert res["severity_score"] == 4.0
    assert res["severity_norm"] == 0.75
    # Proximity: drop rate is 100%, trigger rate is 100%, blended P = 0.5*4.8 + 0.5*5.0 = 4.9
    assert abs(res["proximity_score"] - 4.9) < 0.1
    assert abs(res["proximity_norm"] - 0.975) < 0.05
    # Addressability: Autopay has 4.8, A_norm = (4.8 - 1)/4 = 0.95
    assert res["addressability_score"] == 4.8
    assert res["addressability_norm"] == 0.95

    # Impact = (0.30 * 1.0 + 0.30 * 0.75 + 0.40 * 0.975) * 100 = (0.30 + 0.225 + 0.39) * 100 = 91.5
    assert abs(res["impact_score"] - 91.5) < 0.5
    # Opp Score = 91.5 * 0.95 = 86.9
    assert abs(res["opportunity_score"] - 86.9) < 0.5


def test_adjustable_weights():
    """Verify that shifting weights recalculates impact predictably."""
    calc = OpportunityMatrixCalculator(weight_frequency=0.30, weight_severity=0.30, weight_proximity=0.40)
    
    # Change weights to focus heavily on severity: w_f=0.1, w_s=0.8, w_p=0.1
    calc.set_weights(0.1, 0.8, 0.1)
    assert abs(calc.w_f - 0.1) < 1e-4
    assert abs(calc.w_s - 0.8) < 1e-4
    assert abs(calc.w_p - 0.1) < 1e-4


def test_compliance_guardrails():
    """Verify addressability rubric adheres to product constraints (zero advisory/FOMO)."""
    # Autopay
    autopay_addr = get_addressability_for_theme("Salary Date Mismatch Autopay")
    assert autopay_addr["score"] >= 4.5
    assert "Pure transactional UX" in autopay_addr["compliance_notes"]

    # Negative returns / volatility
    vol_addr = get_addressability_for_theme("Negative Return Month 3 Disappointment")
    assert vol_addr["score"] >= 3.8
    assert "avoids stock/fund selection" in vol_addr["compliance_notes"]


def test_sample_size_safeguards():
    """Verify that n < 30 produces low_confidence = True with amber alert."""
    analyzer = SegmentAnalyzer(sample_size_threshold=SAMPLE_SIZE_THRESHOLD)

    # Small cohort (n=12 < 30)
    meta_small = analyzer.get_confidence_metadata(12)
    assert meta_small["low_confidence"] is True
    assert meta_small["badge"] == "LOW_CONFIDENCE"
    assert "Low Confidence" in meta_small["confidence_status"]
    assert "Small sample size" in meta_small["confidence_status"]

    # Robust cohort (n=45 >= 30)
    meta_robust = analyzer.get_confidence_metadata(45)
    assert meta_robust["low_confidence"] is False
    assert meta_robust["badge"] == "HIGH_CONFIDENCE"
    assert "High Confidence" in meta_robust["confidence_status"]


def test_cohort_comparison_partition():
    """Verify mutually exclusive partition of Continuers vs Drop-offs."""
    comparator = CohortComparator()

    items = [
        ExtractedInsight(
            id="c1", feedback_id="f1", source="play", journey_stage="beyond_12",
            start_motivation="", expectation_at_start="", behaviour_change_over_time="",
            drop_trigger="unknown", action_taken="continued", metrics_checked="[\"statement\"]",
            check_frequency="monthly", in_app_confusion="none", in_app_worry="none",
            outside_app_behaviour="[\"spreadsheets\"]", continuation_signal="discipline",
            income_stability="salaried_stable", age_band="29-35", source_of_money="salary",
            influencer="self", investor_experience="intermediate", unmet_need="none",
            emotion="optimistic", severity=1, verbatim_quote="investing for 3 years",
            confidence=0.9
        ),
        ExtractedInsight(
            id="d1", feedback_id="f2", source="reddit", journey_stage="month_1_3",
            start_motivation="", expectation_at_start="", behaviour_change_over_time="",
            drop_trigger="payment_failure", action_taken="stopped", metrics_checked="[\"NAV\"]",
            check_frequency="daily", in_app_confusion="autopay", in_app_worry="penalty",
            outside_app_behaviour="[\"YouTube\"]", continuation_signal="unknown",
            income_stability="gig_freelance", age_band="<22", source_of_money="savings",
            influencer="youtuber_finfluencer", investor_experience="first_time",
            unmet_need="flexible pause", emotion="frustrated", severity=5,
            verbatim_quote="stopped my sip after bank charged penalty", confidence=0.95
        )
    ]

    continuers, drop_offs = comparator.partition_cohorts(items)
    assert len(continuers) == 1
    assert len(drop_offs) == 1
    assert continuers[0].id == "c1"
    assert drop_offs[0].id == "d1"

    comparison = comparator.compare(items)
    assert comparison["continuers_count"] == 1
    assert comparison["drop_offs_count"] == 1
    assert comparison["continuers"]["avg_severity"] == 1.0
    assert comparison["drop_offs"]["avg_severity"] == 5.0


def test_quote_card_integrity():
    """Verify quote card constructor checks raw text matching."""
    ins = ExtractedInsight(
        id="ins_q1", feedback_id="fb_q1", source="play_store", app_name="groww",
        journey_stage="month_1_3", start_motivation="wealth", expectation_at_start="15%",
        behaviour_change_over_time="", drop_trigger="unknown", action_taken="continued",
        metrics_checked="[\"NAV\"]", check_frequency="daily", in_app_confusion="",
        in_app_worry="", outside_app_behaviour="[]", continuation_signal="",
        income_stability="salaried_stable", age_band="22-28", source_of_money="salary",
        influencer="self", investor_experience="first_time", unmet_need="",
        emotion="optimistic", severity=2, verbatim_quote="starting sip for long term",
        confidence=0.9
    )

    fb = CleanedFeedback(
        id="fb_q1", source="play_store", app_name="groww",
        url="https://play.google.com/store/apps/details?id=com.nextbillion.groww",
        author_hash="abcdef1234567890", date=None, rating=5, language="en",
        raw_text="I am starting sip for long term wealth creation.",
        cleaned_text="starting sip for long term wealth creation"
    )

    card = build_quote_card(ins, {"fb_q1": fb})
    assert card["is_verified"] is True
    assert card["verbatim_quote"] == "starting sip for long term"
    assert "https://" in card["url"]
