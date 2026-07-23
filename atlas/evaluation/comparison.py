"""Baseline vs candidate comparison with walk-forward freeze policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from atlas.config.settings import AppConfig
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.bootstrap import BootstrapResult, paired_bootstrap_ci
from atlas.evaluation.evaluator import evaluate_system
from atlas.evaluation.split import split_train_validation
from atlas.evaluation.walk_forward import FoldResult, evaluate_walk_forward_folds
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
    fold_passes: int
    required_fold_passes: int
    folds: tuple[FoldResult, ...]
    bootstrap: BootstrapResult | None
    freeze_policy_version: str
    experiment: ExperimentRecord


def compare_systems(
    baseline: TicketSystem,
    candidate: TicketSystem,
    draws: Sequence[Draw],
    config: AppConfig,
    store: ExperimentStore,
) -> ComparisonResult:
    rules = LotteryRules.from_settings(config.lottery)
    policy = config.evaluation.freeze_policy
    threshold = config.evaluation.min_absolute_delta

    folds = evaluate_walk_forward_folds(
        baseline,
        candidate,
        draws,
        rules,
        config.prizes,
        n_folds=policy.n_folds,
        min_absolute_delta=threshold,
    )
    fold_passes = sum(1 for fold in folds if fold.passed)

    bootstrap: BootstrapResult | None = None
    bootstrap_ok = True
    if policy.bootstrap.enabled:
        bootstrap = paired_bootstrap_ci(
            [fold.delta for fold in folds],
            n_resamples=policy.bootstrap.n_resamples,
            ci_level=policy.bootstrap.ci_level,
            seed=policy.bootstrap.seed,
        )
        bootstrap_ok = bootstrap.ci_lower >= policy.bootstrap.min_ci_lower

    walkforward_ok = fold_passes >= policy.required_fold_passes
    decision = "accepted" if walkforward_ok and bootstrap_ok else "rejected"

    # Holdout diagnostic (does not decide accept/reject).
    _, validation = split_train_validation(draws, config.evaluation.validation_ratio)
    if not validation:
        raise ValueError("Validation window is empty")
    baseline_holdout = evaluate_system(baseline, validation, rules, config.prizes)
    candidate_holdout = evaluate_system(candidate, validation, rules, config.prizes)
    baseline_metric = baseline_holdout.primary_metric
    candidate_metric = candidate_holdout.primary_metric
    delta = candidate_metric - baseline_metric

    if delta > 0:
        outcome = "improved"
    elif delta < 0:
        outcome = "worsened"
    else:
        outcome = "tied"

    evidence = _policy_evidence(
        folds=folds,
        fold_passes=fold_passes,
        required_fold_passes=policy.required_fold_passes,
        bootstrap=bootstrap,
        bootstrap_min_ci_lower=policy.bootstrap.min_ci_lower,
        version=policy.version,
        decision=decision,
    )

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
            "policy_evidence": evidence,
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
        fold_passes=fold_passes,
        required_fold_passes=policy.required_fold_passes,
        folds=tuple(folds),
        bootstrap=bootstrap,
        freeze_policy_version=policy.version,
        experiment=experiment,
    )


def _policy_evidence(
    *,
    folds: Sequence[FoldResult],
    fold_passes: int,
    required_fold_passes: int,
    bootstrap: BootstrapResult | None,
    bootstrap_min_ci_lower: float,
    version: str,
    decision: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "freeze_policy_version": version,
        "fold_passes": fold_passes,
        "required_fold_passes": required_fold_passes,
        "decision": decision,
        "folds": [
            {
                "fold_index": fold.fold_index,
                "contest_start": fold.contest_start,
                "contest_end": fold.contest_end,
                "baseline_metric": fold.baseline_metric,
                "candidate_metric": fold.candidate_metric,
                "delta": fold.delta,
                "passed": fold.passed,
            }
            for fold in folds
        ],
        "bootstrap": None,
    }
    if bootstrap is not None:
        payload["bootstrap"] = {
            "mean_delta": bootstrap.mean_delta,
            "ci_lower": bootstrap.ci_lower,
            "ci_upper": bootstrap.ci_upper,
            "n_resamples": bootstrap.n_resamples,
            "ci_level": bootstrap.ci_level,
            "seed": bootstrap.seed,
            "min_ci_lower": bootstrap_min_ci_lower,
            "passed": bootstrap.ci_lower >= bootstrap_min_ci_lower,
        }
    return payload
