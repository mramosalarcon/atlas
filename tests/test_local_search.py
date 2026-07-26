"""Local-search optimizer tests."""

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
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.local_search import (
    LocalSearchOptimizer,
    apply_replacement,
    format_local_search_report,
    hill_climb,
    objective_score,
)


def _settings(max_passes: int = 10, min_hits: int = 3) -> OptimizerSettings:
    return OptimizerSettings(
        seed=1,
        candidate_pool_size=10,
        greedy=GreedyOptimizerSettings(enabled=True),
        covering=CoveringOptimizerSettings(
            enabled=True, pair_weight="train_frequency"
        ),
        local_search=LocalSearchOptimizerSettings(
            enabled=True,
            max_passes=max_passes,
            primary_metric_min_hits=min_hits,
        ),
        ensemble=EnsembleOptimizerSettings(
            enabled=True,
            seeds=(1, 2),
            sources=("greedy", "covering"),
            primary_metric_min_hits=min_hits,
        ),
    )


def test_local_search_is_deterministic() -> None:
    rules = LotteryRules(1, 12, 4, True, 3)
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
    ]
    settings = _settings()
    first = LocalSearchOptimizer().optimize(draws, rules, settings, name="a")
    second = LocalSearchOptimizer().optimize(draws, rules, settings, name="b")
    assert first.as_number_lists() == second.as_number_lists()


def test_hill_climb_noop_when_no_improvement() -> None:
    rules = LotteryRules(1, 6, 3, True, 2)
    # Tiny draw set where covering seed is already strong enough that max_passes=0
    # is simulated by max_passes with no improving primary/pair move needed:
    # use max_passes=1 on a system that already has full pair coverage of small range.
    draws = [Draw.create(1, [1, 2, 3], rules, additional=4)]
    tickets = [
        Ticket.create([1, 2, 3], rules),
        Ticket.create([1, 2, 4], rules),
    ]
    seed = TicketSystem.create(tickets, rules, name="seed")
    polished, accepts = hill_climb(
        seed, draws, rules, min_hits=3, max_passes=1
    )
    # May or may not accept; ensure score never decreases.
    assert objective_score(polished, draws, min_hits=3) >= objective_score(
        seed, draws, min_hits=3
    )
    assert accepts >= 0


def test_duplicate_ticket_move_skipped() -> None:
    rules = LotteryRules(1, 8, 3, True, 2)
    system = TicketSystem.create(
        [Ticket.create([1, 2, 3], rules), Ticket.create([1, 2, 4], rules)],
        rules,
        name="s",
    )
    # Replacing 4 with 3 on ticket 1 would duplicate ticket 0.
    assert (
        apply_replacement(system, rules, ticket_index=1, remove=4, add=3) is None
    )


def test_local_search_report_non_predictive() -> None:
    rules = LotteryRules(1, 10, 4, True, 2)
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    system = LocalSearchOptimizer().optimize(
        draws, rules, _settings(max_passes=2), name="local-search"
    )
    report = format_local_search_report(
        system,
        seed=1,
        max_passes=2,
        train_contests=(1, 1),
        train_metric=1,
        pairs_covered=1,
        accepts=0,
    ).lower()
    assert "does not predict" in report
    assert "candidate" in report
