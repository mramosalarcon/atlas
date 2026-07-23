"""Walk-forward fold tests."""

from __future__ import annotations

from atlas.config.settings import PrizeSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.walk_forward import (
    evaluate_walk_forward_folds,
    partition_contiguous_folds,
)


def _rules() -> LotteryRules:
    return LotteryRules(1, 56, 6, True, 8)


def _draws(n: int = 6) -> list[Draw]:
    rules = _rules()
    return [
        Draw.create(i, [1, 2, 3, 4, 5, 6], rules, additional=7)
        for i in range(1, n + 1)
    ]


def test_partition_covers_all_draws_without_overlap() -> None:
    draws = _draws(6)
    folds = partition_contiguous_folds(draws, 3)
    assert len(folds) == 3
    flattened = [d.contest for fold in folds for d in fold]
    assert flattened == [1, 2, 3, 4, 5, 6]
    assert all(fold for fold in folds)


def test_fold_pass_fail_vs_delta() -> None:
    rules = _rules()
    prizes = PrizeSettings(True, 20.0, 30.0, 200.0, 5000.0, 50000.0, 1_000_000.0)
    # 4 draws: two weak for candidate, two strong
    draws = [
        Draw.create(1, [50, 51, 52, 53, 54, 55], rules, additional=56),
        Draw.create(2, [50, 51, 52, 53, 54, 55], rules, additional=56),
        Draw.create(3, [1, 2, 3, 10, 20, 30], rules, additional=40),
        Draw.create(4, [1, 2, 3, 4, 20, 30], rules, additional=40),
    ]
    baseline = TicketSystem.create(
        [Ticket.create(t, rules) for t in [
            [7, 8, 9, 10, 11, 12],
            [13, 14, 15, 16, 17, 18],
            [19, 20, 21, 22, 23, 24],
            [25, 26, 27, 28, 29, 30],
            [31, 32, 33, 34, 35, 36],
            [37, 38, 39, 40, 41, 42],
            [43, 44, 45, 46, 47, 48],
            [49, 50, 51, 52, 53, 54],
        ]],
        rules,
        name="baseline",
    )
    candidate = TicketSystem.create(
        [Ticket.create(t, rules) for t in [
            [1, 2, 3, 4, 5, 6],
            [13, 14, 15, 16, 17, 18],
            [19, 20, 21, 22, 23, 24],
            [25, 26, 27, 28, 29, 30],
            [31, 32, 33, 34, 35, 36],
            [37, 38, 39, 40, 41, 42],
            [43, 44, 45, 46, 47, 48],
            [49, 50, 51, 52, 53, 54],
        ]],
        rules,
        name="candidate",
    )
    folds = evaluate_walk_forward_folds(
        baseline,
        candidate,
        draws,
        rules,
        prizes,
        n_folds=2,
        min_absolute_delta=1,
    )
    assert len(folds) == 2
    assert folds[0].passed is False
    assert folds[1].passed is True
