from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, Index, Boolean, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RawFeedback(Base):
    """
    Common schema for raw feedback ingested from all external channels.
    Strictly preserves zero PII (author usernames are salted and SHA-256 hashed).
    """
    __tablename__ = "raw_feedback"

    id = Column(String, primary_key=True)                        # Unique ID (e.g., play_groww_abc123)
    source = Column(String, nullable=False, index=True)          # "play_store" | "app_store" | "reddit" | "youtube" | "forum" | "manual_import"
    app_name = Column(String, nullable=True, index=True)         # "groww", "zerodha_coin", etc.
    url = Column(String, nullable=False)                         # Direct permalink
    author_hash = Column(String(64), nullable=False, index=True) # SHA-256 hash (Zero PII stored)
    date = Column(DateTime, nullable=False, index=True)          # Ingestion / post date in UTC
    rating = Column(Integer, nullable=True)                      # 1 to 5 (where available)
    language = Column(String, nullable=False, default="unknown") # Detected/reported language
    raw_text = Column(Text, nullable=False)                      # Exact unaltered feedback text
    parent_id = Column(String, nullable=True)                    # Parent thread/item ID if applicable
    upvotes_likes = Column(Integer, default=0)                   # Upvotes, likes, or thumbs up
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_source_date", "source", "date"),
        Index("ix_app_source", "app_name", "source"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "app_name": self.app_name,
            "url": self.url,
            "author_hash": self.author_hash,
            "date": self.date.isoformat() if self.date else None,
            "rating": self.rating,
            "language": self.language,
            "raw_text": self.raw_text,
            "parent_id": self.parent_id,
            "upvotes_likes": self.upvotes_likes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class CleanedFeedback(Base):
    """
    Cleaned, deduplicated, and normalized feedback table.
    Preserves exact raw_text for verbatim quote integrity checks.
    """
    __tablename__ = "cleaned_feedback"

    id = Column(String, primary_key=True)                        # Same as RawFeedback.id
    source = Column(String, nullable=False, index=True)
    app_name = Column(String, nullable=True, index=True)
    url = Column(String, nullable=False)
    author_hash = Column(String(64), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    rating = Column(Integer, nullable=True)
    language = Column(String, nullable=False)                    # 'en' | 'hi' | 'hinglish'
    raw_text = Column(Text, nullable=False)                      # Unmodified verbatim text for quote integrity
    cleaned_text = Column(Text, nullable=False)                  # Normalized, de-noised text
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of = Column(String, nullable=True)                 # ID of master item if duplicate
    is_spam = Column(Boolean, default=False, index=True)
    spam_reason = Column(String, nullable=True)
    parent_id = Column(String, nullable=True)
    upvotes_likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_clean_source_date", "source", "date"),
        Index("ix_clean_dup_spam", "is_duplicate", "is_spam"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "app_name": self.app_name,
            "url": self.url,
            "author_hash": self.author_hash,
            "date": self.date.isoformat() if self.date else None,
            "rating": self.rating,
            "language": self.language,
            "raw_text": self.raw_text,
            "cleaned_text": self.cleaned_text,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "is_spam": self.is_spam,
            "spam_reason": self.spam_reason,
            "parent_id": self.parent_id,
            "upvotes_likes": self.upvotes_likes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class ExtractedInsight(Base):
    """
    Pydantic-validated structured insights extracted per relevant feedback item.
    Enforces quote integrity and allows 'unknown' across all qualitative dimensions.
    """
    __tablename__ = "extracted_insights"

    id = Column(String, primary_key=True)                        # ins_<feedback_id>
    feedback_id = Column(String, nullable=False, index=True)     # Foreign reference to raw/cleaned feedback
    source = Column(String, nullable=False, index=True)
    app_name = Column(String, nullable=True, index=True)
    
    # Core Extraction Fields
    journey_stage = Column(String, nullable=False, index=True)   # pre_start | month_1_3 | month_4_12 | etc.
    start_motivation = Column(Text, nullable=False)
    expectation_at_start = Column(Text, nullable=False)
    behaviour_change_over_time = Column(Text, nullable=False)
    drop_trigger = Column(String, nullable=False, index=True)    # payment_failure | cash_crunch | etc.
    action_taken = Column(String, nullable=False, index=True)    # paused | reduced | stopped | continued | etc.
    
    # Check Behavior
    metrics_checked = Column(Text, nullable=False)               # JSON array e.g. ["NAV", "returns"]
    check_frequency = Column(String, nullable=False)             # daily | weekly | monthly | etc.
    
    # In-App Experience
    in_app_confusion = Column(Text, nullable=False)
    in_app_worry = Column(Text, nullable=False)
    
    # External Ecosystem & Continuers
    outside_app_behaviour = Column(Text, nullable=False)         # JSON array e.g. ["YouTube", "Reddit"]
    continuation_signal = Column(Text, nullable=False)
    
    # Demographic & Segment Cues
    income_stability = Column(String, nullable=False, index=True) # salaried_stable | gig_freelance | etc.
    age_band = Column(String, nullable=False)
    source_of_money = Column(String, nullable=False)
    influencer = Column(String, nullable=False, index=True)      # self | friend_colleague | etc.
    investor_experience = Column(String, nullable=False)
    
    # Synthesis & Audit
    unmet_need = Column(Text, nullable=False)
    emotion = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)                   # 1 to 5
    verbatim_quote = Column(Text, nullable=False)                # Exact substring verified from raw_text
    evidence_span = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)                   # 0.0 to 1.0
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_ins_journey_drop", "journey_stage", "drop_trigger"),
        Index("ix_ins_segment", "income_stability", "influencer"),
    )

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "feedback_id": self.feedback_id,
            "source": self.source,
            "app_name": self.app_name,
            "journey_stage": self.journey_stage,
            "start_motivation": self.start_motivation,
            "expectation_at_start": self.expectation_at_start,
            "behaviour_change_over_time": self.behaviour_change_over_time,
            "drop_trigger": self.drop_trigger,
            "action_taken": self.action_taken,
            "metrics_checked": json.loads(self.metrics_checked) if self.metrics_checked.startswith("[") else [self.metrics_checked],
            "check_frequency": self.check_frequency,
            "in_app_confusion": self.in_app_confusion,
            "in_app_worry": self.in_app_worry,
            "outside_app_behaviour": json.loads(self.outside_app_behaviour) if self.outside_app_behaviour.startswith("[") else [self.outside_app_behaviour],
            "continuation_signal": self.continuation_signal,
            "income_stability": self.income_stability,
            "age_band": self.age_band,
            "source_of_money": self.source_of_money,
            "influencer": self.influencer,
            "investor_experience": self.investor_experience,
            "unmet_need": self.unmet_need,
            "emotion": self.emotion,
            "severity": self.severity,
            "verbatim_quote": self.verbatim_quote,
            "evidence_span": self.evidence_span,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Theme(Base):
    """
    Unsupervised thematic clusters discovered via semantic embeddings and HDBSCAN/clustering.
    Distinguishes inductive (emergent) themes from deductive (fixed taxonomy) buckets.
    """
    __tablename__ = "themes"

    id = Column(String, primary_key=True)                        # e.g. "theme_0", "theme_autopay"
    cluster_id = Column(Integer, nullable=False, index=True)     # Raw cluster label (-1 for outliers)
    title = Column(String, nullable=False)                       # LLM-named concise PM title
    description = Column(Text, nullable=False)                  # Description of the problem area
    taxonomy_type = Column(String, nullable=False, default="inductive") # "inductive" | "deductive"
    exemplar_quote_1 = Column(Text, nullable=True)
    exemplar_quote_2 = Column(Text, nullable=True)
    item_count = Column(Integer, default=0)
    avg_severity = Column(Float, default=1.0)
    primary_drop_trigger = Column(String, nullable=True)
    primary_journey_stage = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "title": self.title,
            "description": self.description,
            "taxonomy_type": self.taxonomy_type,
            "exemplar_quote_1": self.exemplar_quote_1,
            "exemplar_quote_2": self.exemplar_quote_2,
            "item_count": self.item_count,
            "avg_severity": round(self.avg_severity, 2) if self.avg_severity else 1.0,
            "primary_drop_trigger": self.primary_drop_trigger,
            "primary_journey_stage": self.primary_journey_stage,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class ItemThemeMapping(Base):
    """
    Maps extracted feedback records to discovered themes with distance scores.
    """
    __tablename__ = "item_theme_mapping"

    id = Column(String, primary_key=True)                        # itm_<feedback_id>_<theme_id>
    feedback_id = Column(String, nullable=False, index=True)
    theme_id = Column(String, nullable=False, index=True)
    distance_score = Column(Float, default=0.0)
    is_outlier = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_id": self.feedback_id,
            "theme_id": self.theme_id,
            "distance_score": self.distance_score,
            "is_outlier": self.is_outlier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class OpportunityScoreRecord(Base):
    """
    Persisted multi-factor Opportunity Matrix scores for discovered behavioral themes.
    Calculates Impact = w_f * F_norm + w_s * S_norm + w_p * P_norm, Opp Score = Impact * A_norm.
    Strictly adheres to product constraints (no FOMO/urgency, no fund recommendations).
    """
    __tablename__ = "opportunity_scores"

    id = Column(String, primary_key=True)                        # opp_<theme_id>
    theme_id = Column(String, nullable=False, index=True)        # References Theme.id
    theme_title = Column(String, nullable=False)
    taxonomy_type = Column(String, nullable=False, default="inductive") # "inductive" | "deductive"
    item_count = Column(Integer, nullable=False, default=0)
    frequency_pct = Column(Float, nullable=False, default=0.0)   # % of total relevant feedback
    frequency_norm = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0
    severity_score = Column(Float, nullable=False, default=1.0)  # 1.0 - 5.0 mean user pain
    severity_norm = Column(Float, nullable=False, default=0.0)   # 0.0 - 1.0
    proximity_score = Column(Float, nullable=False, default=1.0) # 1.0 - 5.0 directness to drop-off
    proximity_norm = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0
    addressability_score = Column(Float, nullable=False, default=1.0) # 1.0 - 5.0 feasibility
    addressability_norm = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0
    impact_score = Column(Float, nullable=False, default=0.0)    # 0.0 - 100.0
    opportunity_score = Column(Float, nullable=False, default=0.0) # 0.0 - 100.0
    trend_velocity = Column(Float, nullable=True, default=0.0)   # Volume growth velocity
    rank = Column(Integer, nullable=False, default=1)
    primary_drop_trigger = Column(String, nullable=True)
    exemplar_quote = Column(Text, nullable=True)
    strategic_rationale = Column(Text, nullable=True)
    addressability_feasibility = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "theme_id": self.theme_id,
            "theme_title": self.theme_title,
            "taxonomy_type": self.taxonomy_type,
            "item_count": self.item_count,
            "frequency_pct": round(self.frequency_pct, 2),
            "frequency_norm": round(self.frequency_norm, 3),
            "severity_score": round(self.severity_score, 2),
            "severity_norm": round(self.severity_norm, 3),
            "proximity_score": round(self.proximity_score, 2),
            "proximity_norm": round(self.proximity_norm, 3),
            "addressability_score": round(self.addressability_score, 2),
            "addressability_norm": round(self.addressability_norm, 3),
            "impact_score": round(self.impact_score, 1),
            "opportunity_score": round(self.opportunity_score, 1),
            "trend_velocity": round(self.trend_velocity, 2) if self.trend_velocity is not None else 0.0,
            "rank": self.rank,
            "primary_drop_trigger": self.primary_drop_trigger,
            "exemplar_quote": self.exemplar_quote,
            "strategic_rationale": self.strategic_rationale,
            "addressability_feasibility": self.addressability_feasibility,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class AuditCorrectionRecord(Base):
    """
    Persistent audit log storing human corrections and overrides of model outputs.
    Mandates a non-empty justification reason and tags failure modes.
    """
    __tablename__ = "audit_corrections"

    id = Column(String, primary_key=True)                        # audit_<id>
    feedback_id = Column(String, nullable=False, index=True)
    field_corrected = Column(String, nullable=False, index=True) # e.g. "drop_trigger", "emotion"
    original_value = Column(String, nullable=False)
    corrected_value = Column(String, nullable=False)
    justification_reason = Column(Text, nullable=False)          # Mandatory rationale
    reviewer_id = Column(String, nullable=False, default="growth_pm_reviewer")
    failure_mode = Column(String, nullable=False, default="multi_topic_complexity") # hinglish_ambiguity, sarcasm_irony, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_id": self.feedback_id,
            "field_corrected": self.field_corrected,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "justification_reason": self.justification_reason,
            "reviewer_id": self.reviewer_id,
            "failure_mode": self.failure_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



