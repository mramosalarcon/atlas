"""Contiguous chronological walk-forward folds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.config.settings import PrizeSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.evaluator import evaluate_system


@dataclass(frozen=True)
class FoldResult:
    fold_index: int
    contest_start: int
    contest_end: int
    baseline_metric: int
    candidate_metric: int
    delta: int
    passed: bool


def partition_contiguous_folds(
    draws: Sequence[Draw],
    n_folds: int,
) -> list[list[Draw]]:
    if n_folds < 2:
        raise ValueError(f"n_folds must be >= 2, got {n_folds}")
    ordered = sorted(draws, key=lambda d: d.contest)
    if len(ordered) < n_folds:
        raise ValueError(
            f"Need at least {n_folds} draws for walk-forward folds, got {len(ordered)}"
        )

    fold_size, remainder = divmod(len(ordered), n_folds)
    folds: list[list[Draw]] = []
    index = 0
    for fold_i in range(n_folds):
        size = fold_size + (1 if fold_i < remainder else 0)
        segment = list(ordered[index : index + size])
        if not segment:
            raise ValueError(f"Fold {fold_i + 1} is empty")
        folds.append(segment)
        index += size
    return folds


def evaluate_walk_forward_folds(
    baseline: TicketSystem,
    candidate: TicketSystem,
    draws: Sequence[Draw],
    rules: LotteryRules,
    prizes: PrizeSettings,
    *,
    n_folds: int,
    min_absolute_delta: int,
) -> list[FoldResult]:
    folds = partition_contiguous_folds(draws, n_folds)
    results: list[FoldResult] = []
    for fold_index, segment in enumerate(folds, start=1):
        baseline_metric = evaluate_system(baseline, segment, rules, prizes).primary_metric
        candidate_metric = evaluate_system(candidate, segment, rules, prizes).primary_metric
        delta = candidate_metric - baseline_metric
        results.append(
            FoldResult(
                fold_index=fold_index,
                contest_start=segment[0].contest,
                contest_end=segment[-1].contest,
                baseline_metric=baseline_metric,
                candidate_metric=candidate_metric,
                delta=delta,
                passed=delta >= min_absolute_delta,
            )
        )
    return results
