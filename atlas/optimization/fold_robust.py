"""Fold-robust local search: covering or file seed, fold-aware hill climb."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.walk_forward import partition_contiguous_folds
from atlas.optimization.covering import CoveringOptimizer
from atlas.optimization.local_search import (
    _coverage_counts,
    apply_replacement,
    pair_coverage_count,
    primary_metric_count,
    quad_coverage_count,
    triple_coverage_count,
)
from atlas.optimization.strategy import OptimizationStrategy


class FoldRobustSeedError(ValueError):
    """Raised when a fold-robust seed file cannot be loaded."""


class FoldRobustBaselineError(ValueError):
    """Raised when a relative-objective baseline cannot be resolved or loaded."""


class FoldRobustOptimizer(OptimizationStrategy):
    """Hill climb with worst-fold-aware or champion-relative train objective."""

    def __init__(
        self,
        *,
        n_folds: int,
        seed_from: Path | None = None,
        objective: str = "absolute",
        relative_baseline: TicketSystem | None = None,
        min_absolute_delta: int = 1,
        relative_baseline_path: str | None = None,
    ) -> None:
        if n_folds < 2:
            raise ValueError(f"n_folds must be >= 2, got {n_folds}")
        if objective not in {"absolute", "relative"}:
            raise ValueError(
                f"objective must be 'absolute' or 'relative', got {objective!r}"
            )
        self.n_folds = n_folds
        self.seed_from = seed_from
        self.objective = objective
        self.relative_baseline = relative_baseline
        self.min_absolute_delta = min_absolute_delta
        self.relative_baseline_path = relative_baseline_path
        self.last_seed_source = "covering"
        self.last_objective = objective
        self.last_accepts = 0
        self.last_train_metric = 0
        self.last_min_fold = 0
        self.last_sum_fold = 0
        self.last_fold_primaries: tuple[int, ...] = ()
        self.last_fold_deltas: tuple[int, ...] = ()
        self.last_train_fold_passes = 0
        self.last_sum_deltas = 0
        self.last_pairs_covered = 0
        self.last_triples_covered = 0
        self.last_quads_covered = 0

    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "fold-robust",
    ) -> TicketSystem:
        if not settings.fold_robust.enabled:
            raise ValueError("Fold-robust optimizer is disabled in config")
        _ = settings.seed

        objective = self.objective
        self.last_objective = objective
        baseline_fold_primaries: tuple[int, ...] | None = None
        if objective == "relative":
            if self.relative_baseline is None:
                raise FoldRobustBaselineError(
                    "relative objective requires a baseline TicketSystem"
                )
            baseline_fold_primaries = fold_primary_metrics(
                self.relative_baseline,
                draws,
                min_hits=settings.fold_robust.primary_metric_min_hits,
                n_folds=self.n_folds,
            )

        seed_path = self.seed_from
        if seed_path is not None:
            seed_system = load_fold_robust_seed(
                seed_path, rules, name=f"{name}-seed"
            )
            self.last_seed_source = str(seed_path)
        else:
            seed_system = CoveringOptimizer().optimize(
                draws, rules, settings, name=f"{name}-seed"
            )
            self.last_seed_source = "covering"

        polished, accepts = fold_robust_hill_climb(
            seed_system,
            draws,
            rules,
            min_hits=settings.fold_robust.primary_metric_min_hits,
            max_passes=settings.fold_robust.max_passes,
            n_folds=self.n_folds,
            objective=objective,
            baseline_fold_primaries=baseline_fold_primaries,
            min_absolute_delta=self.min_absolute_delta,
        )
        result = TicketSystem.create(list(polished.tickets), rules, name=name)
        fold_primaries = fold_primary_metrics(
            result,
            draws,
            min_hits=settings.fold_robust.primary_metric_min_hits,
            n_folds=self.n_folds,
        )
        abs_score = fold_robust_score(
            result,
            draws,
            min_hits=settings.fold_robust.primary_metric_min_hits,
            n_folds=self.n_folds,
        )
        self.last_accepts = accepts
        self.last_min_fold = abs_score[0]
        self.last_sum_fold = abs_score[1]
        self.last_train_metric = abs_score[2]
        self.last_pairs_covered = abs_score[3]
        self.last_triples_covered = abs_score[4]
        self.last_quads_covered = abs_score[5]
        self.last_fold_primaries = fold_primaries
        if baseline_fold_primaries is not None:
            deltas = tuple(
                cand - base
                for cand, base in zip(fold_primaries, baseline_fold_primaries)
            )
            self.last_fold_deltas = deltas
            self.last_sum_deltas = sum(deltas)
            self.last_train_fold_passes = sum(
                1 for delta in deltas if delta >= self.min_absolute_delta
            )
        else:
            self.last_fold_deltas = ()
            self.last_sum_deltas = 0
            self.last_train_fold_passes = 0
        return result


def resolve_relative_baseline_path(
    *,
    cli_relative_to: Path | None,
    relative_to: Path | None,
    seed_from: Path | None,
    tournament_champion: Path | None,
) -> Path:
    for path in (cli_relative_to, relative_to, seed_from, tournament_champion):
        if path is not None:
            return path
    raise FoldRobustBaselineError(
        "relative objective requires a baseline path "
        "(--relative-to, optimizer.fold_robust.relative_to, "
        "optimizer.fold_robust.seed_from, or tournament.champion)"
    )


def load_fold_robust_seed(
    path: Path, rules: LotteryRules, *, name: str
) -> TicketSystem:
    if not path.is_file():
        raise FoldRobustSeedError(f"Fold-robust seed file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FoldRobustSeedError(
            f"Fold-robust seed file is not valid JSON: {path}"
        ) from exc
    if isinstance(payload, dict):
        tickets_raw = payload["tickets"]
        name = str(payload.get("name", name))
    else:
        tickets_raw = payload
    try:
        tickets = [Ticket.create(numbers, rules) for numbers in tickets_raw]
        return TicketSystem.create(tickets, rules, name=name)
    except Exception as exc:
        raise FoldRobustSeedError(
            f"Fold-robust seed file is invalid under lottery rules: {path}"
        ) from exc


def load_fold_robust_baseline(
    path: Path, rules: LotteryRules, *, name: str
) -> TicketSystem:
    try:
        return load_fold_robust_seed(path, rules, name=name)
    except FoldRobustSeedError as exc:
        raise FoldRobustBaselineError(str(exc).replace("seed", "baseline", 1)) from exc


def fold_primary_metrics(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    min_hits: int,
    n_folds: int,
) -> tuple[int, ...]:
    folds = partition_contiguous_folds(draws, n_folds)
    return tuple(
        primary_metric_count(system, fold, min_hits=min_hits) for fold in folds
    )


def fold_robust_score(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    min_hits: int,
    n_folds: int,
) -> tuple[int, int, int, int, int, int]:
    fold_primaries = fold_primary_metrics(
        system, draws, min_hits=min_hits, n_folds=n_folds
    )
    total = primary_metric_count(system, draws, min_hits=min_hits)
    return (
        min(fold_primaries),
        sum(fold_primaries),
        total,
        pair_coverage_count(system),
        triple_coverage_count(system),
        quad_coverage_count(system),
    )


def fold_relative_score(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    min_hits: int,
    n_folds: int,
    baseline_fold_primaries: Sequence[int],
    min_absolute_delta: int,
) -> tuple[int, ...]:
    fold_primaries = fold_primary_metrics(
        system, draws, min_hits=min_hits, n_folds=n_folds
    )
    if len(fold_primaries) != len(baseline_fold_primaries):
        raise ValueError("baseline fold count must match candidate fold count")
    deltas = [
        cand - base for cand, base in zip(fold_primaries, baseline_fold_primaries)
    ]
    total = primary_metric_count(system, draws, min_hits=min_hits)
    return (
        sum(1 for delta in deltas if delta >= min_absolute_delta),
        sum(deltas),
        min(fold_primaries),
        sum(fold_primaries),
        total,
        pair_coverage_count(system),
        triple_coverage_count(system),
        quad_coverage_count(system),
    )


def _score_from_hits(
    hits: list[list[int]],
    fold_ranges: list[tuple[int, int]],
    ticket_numbers: Sequence[tuple[int, ...]],
    *,
    min_hits: int,
    objective: str = "absolute",
    baseline_fold_primaries: Sequence[int] | None = None,
    min_absolute_delta: int = 1,
) -> tuple[int, ...]:
    fold_primaries: list[int] = []
    total = 0
    for start, end in fold_ranges:
        count = 0
        for draw_idx in range(start, end):
            if max(hits[draw_idx]) >= min_hits:
                count += 1
                total += 1
        fold_primaries.append(count)
    pairs, triples, quads = _coverage_counts(ticket_numbers)
    if objective == "relative":
        if baseline_fold_primaries is None:
            raise ValueError("relative scoring requires baseline_fold_primaries")
        deltas = [
            cand - base
            for cand, base in zip(fold_primaries, baseline_fold_primaries)
        ]
        return (
            sum(1 for delta in deltas if delta >= min_absolute_delta),
            sum(deltas),
            min(fold_primaries),
            sum(fold_primaries),
            total,
            pairs,
            triples,
            quads,
        )
    return (
        min(fold_primaries),
        sum(fold_primaries),
        total,
        pairs,
        triples,
        quads,
    )


def fold_robust_hill_climb(
    seed: TicketSystem,
    draws: Sequence[Draw],
    rules: LotteryRules,
    *,
    min_hits: int,
    max_passes: int,
    n_folds: int,
    objective: str = "absolute",
    baseline_fold_primaries: Sequence[int] | None = None,
    min_absolute_delta: int = 1,
) -> tuple[TicketSystem, int]:
    if objective == "relative" and baseline_fold_primaries is None:
        raise FoldRobustBaselineError(
            "relative objective requires baseline_fold_primaries"
        )
    ordered = sorted(draws, key=lambda d: d.contest)
    folds = partition_contiguous_folds(ordered, n_folds)
    fold_ranges: list[tuple[int, int]] = []
    index = 0
    for fold in folds:
        fold_ranges.append((index, index + len(fold)))
        index += len(fold)

    draw_sets = [frozenset(draw.mains) for draw in ordered]
    ticket_sets = [frozenset(t.numbers) for t in seed.tickets]
    hits = [
        [len(ticket_set & draw_set) for ticket_set in ticket_sets]
        for draw_set in draw_sets
    ]
    current_numbers = [t.numbers for t in seed.tickets]
    best_score = _score_from_hits(
        hits,
        fold_ranges,
        current_numbers,
        min_hits=min_hits,
        objective=objective,
        baseline_fold_primaries=baseline_fold_primaries,
        min_absolute_delta=min_absolute_delta,
    )
    accepts = 0
    population = list(range(rules.min_number, rules.max_number + 1))

    for _ in range(max_passes):
        improved = False
        for ticket_index, numbers in enumerate(current_numbers):
            others = {
                nums for idx, nums in enumerate(current_numbers) if idx != ticket_index
            }
            for remove in numbers:
                for add in population:
                    if add in numbers:
                        continue
                    replacement = tuple(
                        sorted(n for n in numbers if n != remove) + [add]
                    )
                    if replacement in others:
                        continue
                    new_set = frozenset(replacement)
                    fold_primaries: list[int] = []
                    total = 0
                    for start, end in fold_ranges:
                        count = 0
                        for draw_idx in range(start, end):
                            row = hits[draw_idx]
                            new_hits = len(new_set & draw_sets[draw_idx])
                            best = new_hits
                            for idx, value in enumerate(row):
                                if idx == ticket_index:
                                    continue
                                if value > best:
                                    best = value
                            if best >= min_hits:
                                count += 1
                                total += 1
                        fold_primaries.append(count)
                    trial_tickets = list(current_numbers)
                    trial_tickets[ticket_index] = replacement
                    pairs, triples, quads = _coverage_counts(trial_tickets)
                    if objective == "relative":
                        assert baseline_fold_primaries is not None
                        deltas = [
                            cand - base
                            for cand, base in zip(
                                fold_primaries, baseline_fold_primaries
                            )
                        ]
                        new_score: tuple[int, ...] = (
                            sum(
                                1
                                for delta in deltas
                                if delta >= min_absolute_delta
                            ),
                            sum(deltas),
                            min(fold_primaries),
                            sum(fold_primaries),
                            total,
                            pairs,
                            triples,
                            quads,
                        )
                    else:
                        new_score = (
                            min(fold_primaries),
                            sum(fold_primaries),
                            total,
                            pairs,
                            triples,
                            quads,
                        )
                    if new_score <= best_score:
                        continue

                    current_numbers = trial_tickets
                    ticket_sets[ticket_index] = new_set
                    for draw_idx, draw_set in enumerate(draw_sets):
                        hits[draw_idx][ticket_index] = len(new_set & draw_set)
                    best_score = new_score
                    accepts += 1
                    improved = True
                    break
                if improved:
                    break
            if improved:
                break
        if not improved:
            break

    tickets = [Ticket.create(nums, rules) for nums in current_numbers]
    return TicketSystem.create(tickets, rules, name=seed.name), accepts


def format_fold_robust_report(
    system: TicketSystem,
    *,
    seed: int,
    max_passes: int,
    n_folds: int,
    train_contests: tuple[int, int] | None,
    min_fold: int,
    sum_fold: int,
    train_metric: int,
    fold_primaries: Sequence[int],
    pairs_covered: int,
    accepts: int,
    triples_covered: int = 0,
    quads_covered: int = 0,
    seed_source: str = "covering",
    objective: str = "absolute",
    relative_baseline: str | None = None,
    fold_deltas: Sequence[int] | None = None,
    train_fold_passes: int | None = None,
    sum_deltas: int | None = None,
    min_absolute_delta: int | None = None,
) -> str:
    contest_line = (
        f"Train contests used for search: {train_contests[0]}–{train_contests[1]}\n"
        if train_contests
        else ""
    )
    fold_lines = "\n".join(
        f"  fold {idx + 1} train primary: {value}"
        for idx, value in enumerate(fold_primaries)
    )
    relative_block = ""
    if objective == "relative":
        delta_lines = ""
        if fold_deltas is not None:
            delta_lines = "\n".join(
                f"  fold {idx + 1} train delta: {value}"
                for idx, value in enumerate(fold_deltas)
            )
            delta_lines = f"Per-fold train deltas vs baseline:\n{delta_lines}\n"
        relative_block = (
            f"Objective: relative (train heuristic; freeze compare is authoritative)\n"
            f"Relative baseline: {relative_baseline or 'unknown'}\n"
            f"Train fold passes (delta >= {min_absolute_delta}): "
            f"{train_fold_passes}\n"
            f"Sum of train fold deltas: {sum_deltas}\n"
            f"{delta_lines}"
        )
    else:
        relative_block = "Objective: absolute\n"
    tickets = "\n".join(
        f"  {idx + 1}: {list(ticket.numbers)}"
        for idx, ticket in enumerate(system.tickets)
    )
    return (
        "ATLAS fold-robust optimize — comparison candidate from historical train "
        "search only; does not predict the next draw and is not auto-accepted.\n"
        f"System: {system.name}\n"
        f"RNG seed: {seed}\n"
        f"Ticket seed source: {seed_source}\n"
        f"{relative_block}"
        f"Max passes: {max_passes}\n"
        f"Folds: {n_folds}\n"
        f"Accepted moves: {accepts}\n"
        f"{contest_line}"
        f"Min fold primary: {min_fold}\n"
        f"Sum fold primary: {sum_fold}\n"
        f"Train primary-metric count: {train_metric}\n"
        f"Per-fold train primaries:\n{fold_lines}\n"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Unordered triples covered: {triples_covered}\n"
        f"Unordered quads covered: {quads_covered}\n"
        f"Tickets:\n{tickets}\n"
    )


# Re-export for tests that assert move legality via shared helper.
__all__ = [
    "FoldRobustBaselineError",
    "FoldRobustOptimizer",
    "FoldRobustSeedError",
    "apply_replacement",
    "fold_primary_metrics",
    "fold_relative_score",
    "fold_robust_hill_climb",
    "fold_robust_score",
    "format_fold_robust_report",
    "load_fold_robust_baseline",
    "load_fold_robust_seed",
    "resolve_relative_baseline_path",
]
