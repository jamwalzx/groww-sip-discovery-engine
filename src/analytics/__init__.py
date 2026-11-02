"""
Analytics module for the First-Time Mutual Fund SIP Continuation Engine.
Provides Opportunity Matrix formulation, Segment cross-tabulations,
Continuer vs Drop-off cohort analytics, and Core Question Q1-Q9 pre-aggregated views.
"""

from .opportunity_matrix import (
    OpportunityMatrixCalculator,
    THEME_ADDRESSABILITY_RUBRIC,
    get_addressability_for_theme,
    normalize_value
)
from .segmentation import SegmentAnalyzer, SAMPLE_SIZE_THRESHOLD
from .cohort_comparison import CohortComparator
from .question_views import QuestionViewAggregator, build_quote_card

__all__ = [
    "OpportunityMatrixCalculator",
    "THEME_ADDRESSABILITY_RUBRIC",
    "get_addressability_for_theme",
    "normalize_value",
    "SegmentAnalyzer",
    "SAMPLE_SIZE_THRESHOLD",
    "CohortComparator",
    "QuestionViewAggregator",
    "build_quote_card",
]

