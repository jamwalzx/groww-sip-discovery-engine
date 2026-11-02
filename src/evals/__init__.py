"""
Evaluation Harness & Quality Assurance module for Groww AI Discovery Engine.
Provides Human-in-the-Loop Golden Dataset, Cohen's Kappa agreement metrics,
Failure Taxonomy classifier, Audit Correction Log, and Source Bias Panel.
"""

from .golden_set import (
    get_golden_benchmark,
    export_golden_set_csv,
    load_golden_set_csv,
    GOLDEN_BENCHMARK_ITEMS
)
from .metrics import (
    compute_accuracy,
    compute_cohens_kappa,
    compute_quote_integrity,
    EvaluationHarness
)
from .failure_taxonomy import (
    FailureTaxonomyClassifier,
    FAILURE_TAXONOMY_CATEGORIES
)
from .audit_log import (
    AuditLogManager,
    PRESEEDED_AUDIT_CASES
)
from .bias_panel import (
    SourceBiasAuditor,
    PLATFORM_CHARACTERISTICS
)

__all__ = [
    "get_golden_benchmark",
    "export_golden_set_csv",
    "load_golden_set_csv",
    "GOLDEN_BENCHMARK_ITEMS",
    "compute_accuracy",
    "compute_cohens_kappa",
    "compute_quote_integrity",
    "EvaluationHarness",
    "FailureTaxonomyClassifier",
    "FAILURE_TAXONOMY_CATEGORIES",
    "AuditLogManager",
    "PRESEEDED_AUDIT_CASES",
    "SourceBiasAuditor",
    "PLATFORM_CHARACTERISTICS",
]

