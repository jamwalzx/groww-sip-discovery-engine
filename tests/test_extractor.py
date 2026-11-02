import pytest
from src.pipeline.schemas import ExtractedInsightSchema, CheckBehaviour, SegmentCues
from src.pipeline.relevance_filter import RelevanceFilter
from src.pipeline.extractor import StructuredExtractor

def test_pydantic_schema_validation():
    # Test valid schema creation
    schema = ExtractedInsightSchema(
        journey_stage="month_1_3",
        start_motivation="wealth creation",
        expectation_at_start="15% returns",
        drop_trigger="underwhelming_returns",
        action_taken="paused",
        check_behaviour=CheckBehaviour(metrics_checked=["NAV", "returns"], frequency="daily"),
        segment_cues=SegmentCues(income_stability="salaried_stable", influencer="friend_colleague"),
        severity=4,
        verbatim_quote="Returns are negative after 2 months",
        confidence=0.92
    )

    assert schema.journey_stage == "month_1_3"
    assert schema.severity == 4
    assert schema.confidence == 0.92
    assert "NAV" in schema.check_behaviour.metrics_checked

def test_schema_unknown_defaults():
    # Ensure all fields default to 'unknown' safely without crashing
    empty_schema = ExtractedInsightSchema(
        verbatim_quote="Arbitrary sample quote text"
    )
    assert empty_schema.journey_stage == "unknown"
    assert empty_schema.drop_trigger == "unknown"
    assert empty_schema.action_taken == "unknown"
    assert empty_schema.segment_cues.income_stability == "unknown"
    assert empty_schema.severity == 1

def test_quote_integrity_assertion():
    extractor = StructuredExtractor()
    raw_text = "Bank charged 590 rs mandate bounce fee because debit date was 1st and salary came on 3rd. Stopped SIP forever."
    
    # Extract
    extracted = extractor.extract(raw_text)
    
    # Crucial assertion: quote MUST be an exact substring of raw_text
    assert extracted.verbatim_quote in raw_text, (
        f"Quote hallucination detected! Quote: '{extracted.verbatim_quote}' not in Raw: '{raw_text}'"
    )
    assert extracted.drop_trigger == "payment_failure"
    assert extracted.action_taken == "stopped"
    assert extracted.severity == 5

def test_relevance_filter():
    rf = RelevanceFilter()

    # 1. Relevant SIP conversation
    sip_text = "I have been doing SIP of 2000 in Parag Parikh for 5 months on Groww. Very worried about negative returns."
    is_rel, reason, conf = rf.evaluate(sip_text)
    assert is_rel is True

    # 2. Irrelevant KYC ticket
    kyc_text = "kyc pending"
    is_rel_kyc, reason_kyc, _ = rf.evaluate(kyc_text)
    assert is_rel_kyc is False

    # 3. One word review
    one_word = "good app"
    is_rel_word, _, _ = rf.evaluate(one_word)
    assert is_rel_word is False

