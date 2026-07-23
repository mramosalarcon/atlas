"""Baseline vs candidate comparison with freeze policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.config.settings import AppConfig
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.evaluator import evaluate_system
from atlas.evaluation.split import split_train_validation
from atlas.infrastructure.experiment_store import ExperimentRecord, ExperimentStore


@dataclass(frozen=True)
class ComparisonResult:
    outcome: str
    decision: str
    baseline_metric: int
    candidate_metric: int
    delta: int
    validation_start: int
    validation_end: int
    min_absolute_delta: int
    experiment: ExperimentRecord


def compare_systems(
    baseline: TicketSystem,
    candidate: TicketSystem,
    draws: Sequence[Draw],
    config: AppConfig,
    store: ExperimentStore,
) -> ComparisonResult:
    rules = LotteryRules.from_settings(config.lottery)
    _, validation = split_train_validation(draws, config.evaluation.validation_ratio)
    if not validation:
        raise ValueError("Validation window is empty")

    baseline_result = evaluate_system(baseline, validation, rules, config.prizes)
    candidate_result = evaluate_system(candidate, validation, rules, config.prizes)

    baseline_metric = baseline_result.primary_metric
    candidate_metric = candidate_result.primary_metric
    delta = candidate_metric - baseline_metric
    threshold = config.evaluation.min_absolute_delta

    if delta > 0:
        outcome = "improved"
    elif delta < 0:
        outcome = "worsened"
    else:
        outcome = "tied"

    decision = "accepted" if delta >= threshold else "rejected"

    experiment = store.append(
        {
            "baseline_name": baseline.name,
            "candidate_name": candidate.name,
            "baseline_tickets": baseline.as_number_lists(),
            "candidate_tickets": candidate.as_number_lists(),
            "validation_start": validation[0].contest,
            "validation_end": validation[-1].contest,
            "baseline_metric": baseline_metric,
            "candidate_metric": candidate_metric,
            "delta": delta,
            "outcome": outcome,
            "decision": decision,
            "min_absolute_delta": threshold,
            "config_path": str(config.source_path),
        }
    )

    return ComparisonResult(
        outcome=outcome,
        decision=decision,
        baseline_metric=baseline_metric,
        candidate_metric=candidate_metric,
        delta=delta,
        validation_start=validation[0].contest,
        validation_end=validation[-1].contest,
        min_absolute_delta=threshold,
        experiment=experiment,
    )
