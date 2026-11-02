from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

class CheckBehaviour(BaseModel):
    """What investors check in the app and how frequently."""
    metrics_checked: List[Literal["NAV", "returns", "XIRR", "statement", "none", "unknown"]] = Field(
        default=["unknown"],
        description="Specific performance metrics or reports the investor checks"
    )
    frequency: Literal["daily", "weekly", "monthly", "only_during_drops", "unknown"] = Field(
        default="unknown",
        description="Cadence of checking behavior"
    )

class SegmentCues(BaseModel):
    """Investor demographic and context cues deduced from feedback."""
    income_stability: Literal["salaried_stable", "gig_freelance", "student_dependent", "irregular_business", "unknown"] = Field(
        default="unknown"
    )
    age_band: Literal["<22", "22-28", "29-35", "36+", "unknown"] = Field(
        default="unknown"
    )
    source_of_money: Literal["salary", "pocket_money", "savings", "windfall", "unknown"] = Field(
        default="unknown"
    )
    influencer: Literal["self", "friend_colleague", "family", "youtuber_finfluencer", "advisor", "app_nudge", "unknown"] = Field(
        default="unknown"
    )
    investor_experience: Literal["first_time", "intermediate", "experienced", "unknown"] = Field(
        default="unknown"
    )

class ExtractedInsightSchema(BaseModel):
    """
    Strict, schema-validated structured extraction model for first-time SIP behavior.
    Validated with Pydantic v2. Temperature = 0.0.
    Every single field allows 'unknown'; model must never guess or hallucinate.
    """
    journey_stage: Literal[
        "pre_start", "month_1_3", "month_4_12", "beyond_12", "paused_or_lapsed", "unknown"
    ] = Field(
        default="unknown",
        description="Investor timeline stage when comment was made"
    )
    start_motivation: str = Field(
        default="unknown",
        description="Why the investor started their SIP (e.g., discipline, wealth creation, tax saving, friend advice)"
    )
    expectation_at_start: str = Field(
        default="unknown",
        description="What the investor expected to happen after starting (e.g., quick gains, steady growth, safety)"
    )
    behaviour_change_over_time: str = Field(
        default="unknown",
        description="Observed change in user behavior since initial start"
    )
    drop_trigger: Literal[
        "payment_failure", "cash_crunch", "income_irregularity", "underwhelming_returns",
        "market_drop", "confusion", "lost_interest", "outside_advice", "switched_platform", "other", "unknown"
    ] = Field(
        default="unknown",
        description="Primary cause leading user to pause, stop, or disengage"
    )
    action_taken: Literal[
        "paused", "reduced", "stopped", "continued", "increased", "switched_fund", "none", "unknown"
    ] = Field(
        default="unknown",
        description="Specific action taken regarding the SIP"
    )
    check_behaviour: CheckBehaviour = Field(
        default_factory=CheckBehaviour
    )
    in_app_confusion: str = Field(
        default="unknown",
        description="Specific in-app UI/UX confusion point (e.g. NAV cutoff time, XIRR formula, mandate status)"
    )
    in_app_worry: str = Field(
        default="unknown",
        description="Emotional in-app worry (e.g. red portfolio day, bank bounce charge fear)"
    )
    outside_app_behaviour: List[Literal[
        "YouTube", "WhatsApp_groups", "friends_family", "Google_search", "spreadsheets", "advisors", "Reddit", "unknown"
    ]] = Field(
        default=["unknown"],
        description="Channels consulted when feeling uncertain outside Groww"
    )
    continuation_signal: str = Field(
        default="unknown",
        description="Signals or positive habits that help continuers persist (e.g. salary date buffer, avoiding daily NAV)"
    )
    segment_cues: SegmentCues = Field(
        default_factory=SegmentCues
    )
    unmet_need: str = Field(
        default="unknown",
        description="Clear, short phrase capturing unmet product need (e.g. advance debit reminder, emergency pause, layman returns explainer)"
    )
    emotion: Literal[
        "optimistic", "anxious", "frustrated", "confused", "detached", "disappointed", "unknown"
    ] = Field(
        default="unknown",
        description="Primary sentiment/emotion conveyed"
    )
    severity: int = Field(
        default=1,
        ge=1,
        le=5,
        description="User friction/distress severity scale from 1 (minor query) to 5 (rage quitting, penalty fees, stopping SIP)"
    )
    verbatim_quote: str = Field(
        description="Exact verbatim substring from raw_text evidencing the extraction"
    )
    evidence_span: Optional[str] = Field(
        default="unknown",
        description="Span or supporting sentence"
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score"
    )

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity(cls, v):
        try:
            val = int(v)
            return max(1, min(5, val))
        except Exception:
            return 1

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, v):
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except Exception:
            return 0.8

