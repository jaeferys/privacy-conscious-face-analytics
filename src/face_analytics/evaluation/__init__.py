"""Reproducible detector robustness evaluation without demographic inference."""

from face_analytics.evaluation.robustness import (
    EvaluationReport,
    EvaluationSample,
    Metrics,
    ScoredBox,
    evaluate_samples,
    run_manifest_evaluation,
    write_report,
)

__all__ = [
    "EvaluationReport",
    "EvaluationSample",
    "Metrics",
    "ScoredBox",
    "evaluate_samples",
    "run_manifest_evaluation",
    "write_report",
]
