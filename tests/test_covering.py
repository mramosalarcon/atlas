"""Covering optimizer tests."""

from __future__ import annotations

from atlas.config.settings import (
    CoveringOptimizerSettings,
    EnsembleOptimizerSettings,
    GreedyOptimizerSettings,
    LocalSearchOptimizerSettings,
    OptimizerSettings,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.optimization.covering import (
    CoveringOptimizer,
    best_pair,
    build_pair_weights,
    construct_ticket,
    format_covering_report,
)


def _settings(pair_weight: str = "train_frequency", seed: int = 1) -> OptimizerSettings:
    return OptimizerSettings(
        seed=seed,
        candidate_pool_size=10,
        greedy=GreedyOptimizerSettings(enabled=True),
        covering=CoveringOptimizerSettings(enabled=True, pair_weight=pair_weight),
        local_search=LocalSearchOptimizerSettings(
            enabled=True, max_passes=5, primary_metric_min_hits=3
        ),
        ensemble=EnsembleOptimizerSettings(
            enabled=True,
            seeds=(1, 2),
            sources=("greedy", "covering"),
            primary_metric_min_hits=3,
        ),
    )


def test_seeds_from_top_uncovered_pair() -> None:
    rules = LotteryRules(1, 8, 4, True, 1)
    weights = {(1, 2): 5.0, (3, 4): 1.0, (5, 6): 1.0}
    # pad remaining pairs with zeros so construct has a full map optional —
    # construct only needs uncovered dict; seed uses best_pair
    ticket = construct_ticket(dict(weights), rules)
    assert 1 in ticket.numbers and 2 in ticket.numbers


def test_train_frequency_orders_common_pairs_first() -> None:
    rules = LotteryRules(1, 6, 3, True, 1)
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 5], rules, additional=4),
        Draw.create(3, [3, 4, 5], rules, additional=6),
    ]
    weights = build_pair_weights(draws, rules, pair_weight="train_frequency")
    assert weights[(1, 2)] > weights[(3, 4)]
    assert best_pair(weights) == (1, 2)


def test_uniform_mode_is_lex_stable() -> None:
    rules = LotteryRules(1, 5, 3, True, 1)
    weights = build_pair_weights([], rules, pair_weight="uniform")
    assert best_pair(weights) == (1, 2)
    ordered = sorted(weights.keys(), key=lambda pair: (-weights[pair], pair))
    assert ordered[0] == (1, 2)
    assert ordered[1] == (1, 3)


def test_covering_is_deterministic() -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
    ]
    settings = _settings(seed=7)
    first = CoveringOptimizer().optimize(draws, rules, settings, name="c1")
    second = CoveringOptimizer().optimize(draws, rules, settings, name="c2")
    assert first.as_number_lists() == second.as_number_lists()
    assert len(first.tickets) == 3


def test_covering_report_non_predictive() -> None:
    rules = LotteryRules(1, 10, 4, True, 2)
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    system = CoveringOptimizer().optimize(
        draws, rules, _settings(), name="covering"
    )
    report = format_covering_report(
        system,
        seed=1,
        pair_weight="train_frequency",
        train_contests=(1, 1),
        pairs_covered=1,
    ).lower()
    assert "does not predict" in report
    assert "candidate" in report
