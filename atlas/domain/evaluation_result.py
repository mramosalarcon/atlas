"""Evaluation result value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemEvaluationResult:
    draws_evaluated: int
    hits_at_least_3: int
    hits_at_least_4: int
    hits_at_least_5: int
    hits_at_least_6: int
    coverage_ratio_ge3: float
    total_cost: float
    total_prizes: float
    roi: float
    prizes_provisional: bool

    @property
    def primary_metric(self) -> int:
        return self.hits_at_least_3
