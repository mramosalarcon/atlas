"""Greedy optimizer tests."""

from __future__ import annotations

from atlas.config.settings import (
    CoveringOptimizerSettings,
    GreedyOptimizerSettings,
    OptimizerSettings,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.optimization.greedy import (
    GreedyOptimizer,
    format_optimize_report,
    generate_candidate_tickets,
)
from atlas.optimization.pairs import coverage_union, new_pair_count


def _settings(seed: int = 1, pool: int = 40) -> OptimizerSettings:
    return OptimizerSettings(
        seed=seed,
        candidate_pool_size=pool,
        greedy=GreedyOptimizerSettings(enabled=True),
        covering=CoveringOptimizerSettings(
            enabled=True, pair_weight="train_frequency"
        ),
    )


def test_generate_candidates_respects_pool_size() -> None:
    import random

    rules = LotteryRules(1, 12, 4, True, 8)
    tickets = generate_candidate_tickets(
        rules, pool_size=10, rng=random.Random(0), exclude=set()
    )
    assert len(tickets) == 10
    assert len({t.numbers for t in tickets}) == 10


def test_greedy_is_deterministic() -> None:
    rules = LotteryRules(1, 16, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [5, 6, 7, 8], rules, additional=9),
    ]
    settings = _settings(seed=99, pool=30)
    first = GreedyOptimizer().optimize(draws, rules, settings, name="g1")
    second = GreedyOptimizer().optimize(draws, rules, settings, name="g2")
    assert first.as_number_lists() == second.as_number_lists()
    assert len(first.tickets) == 3


def test_greedy_prefers_new_pairs() -> None:
    rules = LotteryRules(1, 10, 3, True, 2)
    # Force a tiny pool where one ticket overlaps heavily and another adds new pairs.
    candidates = [
        Ticket.create([1, 2, 3], rules),
        Ticket.create([1, 2, 4], rules),
        Ticket.create([5, 6, 7], rules),
    ]
    covered = coverage_union([candidates[0]])
    scored = sorted(
        candidates[1:],
        key=lambda t: (-new_pair_count(t, covered), t.numbers),
    )
    assert scored[0].numbers == (5, 6, 7)


def test_optimize_report_non_predictive() -> None:
    rules = LotteryRules(1, 12, 4, True, 2)
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    system = GreedyOptimizer().optimize(draws, rules, _settings(pool=20), name="greedy")
    report = format_optimize_report(
        system, seed=1, train_contests=(1, 1), pairs_covered=1
    ).lower()
    assert "does not predict" in report
    assert "candidate" in report
