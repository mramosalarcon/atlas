"""Fold-robust optimizer tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.config.settings import (
    CoveringOptimizerSettings,
    EnsembleOptimizerSettings,
    FoldRobustOptimizerSettings,
    GreedyOptimizerSettings,
    LocalSearchOptimizerSettings,
    OptimizerSettings,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.fold_robust import (
    FoldRobustBaselineError,
    FoldRobustOptimizer,
    FoldRobustSeedError,
    apply_replacement,
    fold_primary_metrics,
    fold_relative_score,
    fold_robust_hill_climb,
    fold_robust_score,
    format_fold_robust_report,
    resolve_relative_baseline_path,
)
from atlas.optimization.local_search import primary_metric_count


def _settings(max_passes: int = 5, min_hits: int = 3) -> OptimizerSettings:
    return OptimizerSettings(
        seed=1,
        candidate_pool_size=10,
        greedy=GreedyOptimizerSettings(enabled=True),
        covering=CoveringOptimizerSettings(
            enabled=True, pair_weight="train_frequency"
        ),
        local_search=LocalSearchOptimizerSettings(
            enabled=True, max_passes=max_passes, primary_metric_min_hits=min_hits
        ),
        ensemble=EnsembleOptimizerSettings(
            enabled=True,
            seeds=(1, 2),
            sources=("greedy", "covering"),
            primary_metric_min_hits=min_hits,
        ),
        fold_robust=FoldRobustOptimizerSettings(
            enabled=True,
            max_passes=max_passes,
            primary_metric_min_hits=min_hits,
        ),
    )


def test_fold_robust_is_deterministic() -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
        Draw.create(4, [1, 3, 5, 7], rules, additional=8),
    ]
    settings = _settings()
    first_opt = FoldRobustOptimizer(n_folds=2)
    first = first_opt.optimize(draws, rules, settings, name="a")
    second = FoldRobustOptimizer(n_folds=2).optimize(draws, rules, settings, name="b")
    assert first.as_number_lists() == second.as_number_lists()
    assert first_opt.last_seed_source == "covering"


def test_min_fold_preferred_over_aggregate_only() -> None:
    rules = LotteryRules(1, 10, 3, True, 2)
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 3], rules, additional=4),
        Draw.create(3, [7, 8, 9], rules, additional=10),
        Draw.create(4, [7, 8, 9], rules, additional=10),
    ]
    unbalanced = TicketSystem.create(
        [
            Ticket.create([1, 2, 3], rules),
            Ticket.create([1, 2, 4], rules),
        ],
        rules,
        name="unbalanced",
    )
    balanced = TicketSystem.create(
        [
            Ticket.create([1, 2, 3], rules),
            Ticket.create([7, 8, 9], rules),
        ],
        rules,
        name="balanced",
    )
    unbalanced_score = fold_robust_score(
        unbalanced, draws, min_hits=3, n_folds=2
    )
    balanced_score = fold_robust_score(balanced, draws, min_hits=3, n_folds=2)
    assert balanced_score[0] > unbalanced_score[0]
    assert primary_metric_count(unbalanced, draws, min_hits=3) == 2
    assert primary_metric_count(balanced, draws, min_hits=3) == 4


def test_hill_climb_accepts_min_fold_improvement() -> None:
    rules = LotteryRules(1, 10, 3, True, 2)
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 3], rules, additional=4),
        Draw.create(3, [7, 8, 9], rules, additional=10),
        Draw.create(4, [7, 8, 9], rules, additional=10),
    ]
    seed = TicketSystem.create(
        [
            Ticket.create([1, 2, 3], rules),
            Ticket.create([1, 2, 4], rules),
        ],
        rules,
        name="seed",
    )
    polished, accepts = fold_robust_hill_climb(
        seed, draws, rules, min_hits=3, max_passes=5, n_folds=2
    )
    assert accepts >= 1
    assert fold_robust_score(polished, draws, min_hits=3, n_folds=2) > fold_robust_score(
        seed, draws, min_hits=3, n_folds=2
    )


def test_duplicate_ticket_move_skipped() -> None:
    rules = LotteryRules(1, 8, 3, True, 2)
    system = TicketSystem.create(
        [Ticket.create([1, 2, 3], rules), Ticket.create([1, 2, 4], rules)],
        rules,
        name="s",
    )
    assert (
        apply_replacement(system, rules, ticket_index=1, remove=4, add=3) is None
    )


def test_file_seed_used_and_deterministic(tmp_path: Path) -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
        Draw.create(4, [1, 3, 5, 7], rules, additional=8),
    ]
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "name": "seed",
                "tickets": [
                    [1, 2, 3, 4],
                    [5, 6, 7, 8],
                    [9, 10, 11, 12],
                ],
            }
        ),
        encoding="utf-8",
    )
    settings = _settings(max_passes=2)
    first = FoldRobustOptimizer(n_folds=2, seed_from=seed_path).optimize(
        draws, rules, settings, name="a"
    )
    second_opt = FoldRobustOptimizer(n_folds=2, seed_from=seed_path)
    second = second_opt.optimize(draws, rules, settings, name="b")
    assert first.as_number_lists() == second.as_number_lists()
    assert second_opt.last_seed_source == str(seed_path)


def test_missing_seed_file_fails(tmp_path: Path) -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    missing = tmp_path / "missing.json"
    with pytest.raises(FoldRobustSeedError, match="not found"):
        FoldRobustOptimizer(n_folds=2, seed_from=missing).optimize(
            draws, rules, _settings(max_passes=1), name="fold-robust"
        )


def test_fold_robust_report_non_predictive() -> None:
    rules = LotteryRules(1, 10, 4, True, 2)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
    ]
    optimizer = FoldRobustOptimizer(n_folds=2)
    system = optimizer.optimize(draws, rules, _settings(max_passes=2), name="fold-robust")
    report = format_fold_robust_report(
        system,
        seed=1,
        max_passes=2,
        n_folds=2,
        train_contests=(1, 2),
        min_fold=optimizer.last_min_fold,
        sum_fold=optimizer.last_sum_fold,
        train_metric=optimizer.last_train_metric,
        fold_primaries=optimizer.last_fold_primaries,
        pairs_covered=optimizer.last_pairs_covered,
        triples_covered=optimizer.last_triples_covered,
        quads_covered=optimizer.last_quads_covered,
        accepts=optimizer.last_accepts,
        seed_source=optimizer.last_seed_source,
    ).lower()
    assert "does not predict" in report
    assert "candidate" in report
    assert "min fold primary" in report
    assert "ticket seed source: covering" in report
    assert "objective: absolute" in report


def test_relative_prefers_extra_fold_pass() -> None:
    rules = LotteryRules(1, 10, 3, True, 2)
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 3], rules, additional=4),
        Draw.create(3, [7, 8, 9], rules, additional=10),
        Draw.create(4, [7, 8, 9], rules, additional=10),
    ]
    baseline = TicketSystem.create(
        [
            Ticket.create([1, 2, 3], rules),
            Ticket.create([1, 2, 4], rules),
        ],
        rules,
        name="baseline",
    )
    stronger = TicketSystem.create(
        [
            Ticket.create([1, 2, 3], rules),
            Ticket.create([7, 8, 9], rules),
        ],
        rules,
        name="stronger",
    )
    base_folds = fold_primary_metrics(baseline, draws, min_hits=3, n_folds=2)
    weak = fold_relative_score(
        baseline,
        draws,
        min_hits=3,
        n_folds=2,
        baseline_fold_primaries=base_folds,
        min_absolute_delta=1,
    )
    strong = fold_relative_score(
        stronger,
        draws,
        min_hits=3,
        n_folds=2,
        baseline_fold_primaries=base_folds,
        min_absolute_delta=1,
    )
    assert strong[0] > weak[0]


def test_relative_missing_baseline_path_errors() -> None:
    with pytest.raises(FoldRobustBaselineError, match="baseline path"):
        resolve_relative_baseline_path(
            cli_relative_to=None,
            relative_to=None,
            seed_from=None,
            tournament_champion=None,
        )


def test_relative_optimize_is_deterministic(tmp_path: Path) -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
        Draw.create(4, [1, 3, 5, 7], rules, additional=8),
    ]
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "name": "seed",
                "tickets": [
                    [1, 2, 3, 4],
                    [5, 6, 7, 8],
                    [9, 10, 11, 12],
                ],
            }
        ),
        encoding="utf-8",
    )
    baseline = TicketSystem.create(
        [
            Ticket.create([1, 2, 3, 4], rules),
            Ticket.create([5, 6, 7, 8], rules),
            Ticket.create([9, 10, 11, 12], rules),
        ],
        rules,
        name="baseline",
    )
    settings = _settings(max_passes=2)
    first = FoldRobustOptimizer(
        n_folds=2,
        seed_from=seed_path,
        objective="relative",
        relative_baseline=baseline,
        min_absolute_delta=1,
    ).optimize(draws, rules, settings, name="a")
    second_opt = FoldRobustOptimizer(
        n_folds=2,
        seed_from=seed_path,
        objective="relative",
        relative_baseline=baseline,
        min_absolute_delta=1,
    )
    second = second_opt.optimize(draws, rules, settings, name="b")
    assert first.as_number_lists() == second.as_number_lists()
    assert second_opt.last_objective == "relative"
    assert len(second_opt.last_fold_deltas) == 2


def test_relative_optimize_without_baseline_fails() -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    with pytest.raises(FoldRobustBaselineError, match="baseline"):
        FoldRobustOptimizer(n_folds=2, objective="relative").optimize(
            draws, rules, _settings(max_passes=1), name="fold-robust"
        )