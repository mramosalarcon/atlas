"""Ensemble optimizer tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.config.settings import (
    CoveringOptimizerSettings,
    EnsembleOptimizerSettings,
    GreedyOptimizerSettings,
    LocalSearchOptimizerSettings,
    OptimizerSettings,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.ensemble import (
    EnsembleOptimizer,
    EnsemblePoolError,
    draft_from_pool,
    format_ensemble_report,
    pool_tickets_from_files,
    pool_tickets_from_systems,
)


def _settings(
    *,
    seeds: tuple[int, ...] = (1, 2),
    sources: tuple[str, ...] = ("greedy", "covering"),
    pool: int = 30,
) -> OptimizerSettings:
    return OptimizerSettings(
        seed=1,
        candidate_pool_size=pool,
        greedy=GreedyOptimizerSettings(enabled=True),
        covering=CoveringOptimizerSettings(
            enabled=True, pair_weight="train_frequency"
        ),
        local_search=LocalSearchOptimizerSettings(
            enabled=True, max_passes=5, primary_metric_min_hits=3
        ),
        ensemble=EnsembleOptimizerSettings(
            enabled=True,
            seeds=seeds,
            sources=sources,
            primary_metric_min_hits=3,
        ),
    )


def _rules(system_size: int = 3) -> LotteryRules:
    return LotteryRules(1, 12, 4, True, system_size)


def _draws(rules: LotteryRules) -> list[Draw]:
    return [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
        Draw.create(4, [2, 3, 4, 5], rules, additional=6),
    ]


def test_pool_deduplicates_tickets() -> None:
    rules = _rules(system_size=2)
    a = TicketSystem.create(
        [Ticket.create([1, 2, 3, 4], rules), Ticket.create([5, 6, 7, 8], rules)],
        rules,
        name="a",
    )
    b = TicketSystem.create(
        [Ticket.create([1, 2, 3, 4], rules), Ticket.create([9, 10, 11, 12], rules)],
        rules,
        name="b",
    )
    pool = pool_tickets_from_systems([a, b])
    assert len(pool) == 3
    assert (1, 2, 3, 4) in pool


def test_draft_size_and_insufficient_pool() -> None:
    rules = _rules(system_size=3)
    draws = _draws(rules)
    tickets = [
        Ticket.create([1, 2, 3, 4], rules),
        Ticket.create([5, 6, 7, 8], rules),
    ]
    pool = {t.numbers: t for t in tickets}
    with pytest.raises(EnsemblePoolError, match="need at least 3"):
        draft_from_pool(pool, draws, rules, min_hits=3)

    tickets.append(Ticket.create([9, 10, 11, 12], rules))
    pool = {t.numbers: t for t in tickets}
    drafted = draft_from_pool(pool, draws, rules, min_hits=3)
    assert len(drafted) == 3
    assert len({t.numbers for t in drafted}) == 3


def test_draft_is_deterministic() -> None:
    rules = _rules(system_size=3)
    draws = _draws(rules)
    tickets = [
        Ticket.create([9, 10, 11, 12], rules),
        Ticket.create([1, 2, 3, 4], rules),
        Ticket.create([5, 6, 7, 8], rules),
        Ticket.create([2, 3, 4, 5], rules),
    ]
    pool = {t.numbers: t for t in tickets}
    a = [t.numbers for t in draft_from_pool(pool, draws, rules, min_hits=3)]
    b = [t.numbers for t in draft_from_pool(pool, draws, rules, min_hits=3)]
    assert a == b


def test_pool_tickets_from_files(tmp_path: Path) -> None:
    rules = _rules(system_size=2)
    path = tmp_path / "sys.json"
    path.write_text(
        json.dumps(
            {
                "name": "sample",
                "tickets": [[1, 2, 3, 4], [5, 6, 7, 8]],
            }
        ),
        encoding="utf-8",
    )
    pool = pool_tickets_from_files([path], rules)
    assert len(pool) == 2


def test_ensemble_optimizer_deterministic() -> None:
    rules = _rules(system_size=3)
    draws = _draws(rules)
    settings = _settings(seeds=(1, 2), sources=("greedy",), pool=40)
    opt = EnsembleOptimizer()
    a = opt.optimize(draws, rules, settings, name="ensemble")
    b = EnsembleOptimizer().optimize(draws, rules, settings, name="ensemble")
    assert a.as_number_lists() == b.as_number_lists()
    assert len(a.tickets) == 3
    assert opt.last_pool_size >= 3


def test_format_ensemble_report_is_non_predictive() -> None:
    rules = _rules(system_size=2)
    system = TicketSystem.create(
        [Ticket.create([1, 2, 3, 4], rules), Ticket.create([5, 6, 7, 8], rules)],
        rules,
        name="ensemble",
    )
    report = format_ensemble_report(
        system,
        seeds=[1, 2],
        sources=["greedy"],
        pool_size=10,
        train_contests=(1, 4),
        train_metric=2,
        pairs_covered=12,
    )
    assert "does not predict" in report
    assert "not auto-accepted" in report
    assert "comparison candidate" in report
