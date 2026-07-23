"""System evaluation tests."""

from __future__ import annotations

import pytest

from atlas.config.settings import PrizeSettings
from atlas.domain.draw import Draw
from atlas.domain.exceptions import InvalidSystemError
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.evaluator import evaluate_system, format_evaluation_report


def _rules() -> LotteryRules:
    return LotteryRules(1, 56, 6, True, 8)


def _prizes() -> PrizeSettings:
    return PrizeSettings(
        provisional=True,
        ticket_cost=20.0,
        hits_3=30.0,
        hits_4=200.0,
        hits_5=5000.0,
        hits_5_plus_additional=50000.0,
        hits_6=1000000.0,
    )


def _system(rules: LotteryRules, tickets: list[list[int]], name: str = "sys") -> TicketSystem:
    return TicketSystem.create([Ticket.create(t, rules) for t in tickets], rules, name=name)


def test_system_size_enforced() -> None:
    rules = _rules()
    with pytest.raises(InvalidSystemError):
        TicketSystem.create([Ticket.create([1, 2, 3, 4, 5, 6], rules)], rules)


def test_aggregate_counts_and_deterministic() -> None:
    rules = _rules()
    prizes = _prizes()
    draws = [
        Draw.create(1, [1, 2, 3, 10, 20, 30], rules, additional=40),
        Draw.create(2, [1, 2, 3, 4, 20, 30], rules, additional=40),
        Draw.create(3, [40, 41, 42, 43, 44, 45], rules, additional=46),
    ]
    tickets = [
        [1, 2, 3, 4, 5, 6],
        [7, 8, 9, 10, 11, 12],
        [13, 14, 15, 16, 17, 18],
        [19, 20, 21, 22, 23, 24],
        [25, 26, 27, 28, 29, 30],
        [31, 32, 33, 34, 35, 36],
        [37, 38, 39, 40, 41, 42],
        [43, 44, 45, 46, 47, 48],
    ]
    system = _system(rules, tickets)
    first = evaluate_system(system, draws, rules, prizes)
    second = evaluate_system(system, draws, rules, prizes)
    assert first == second
    assert first.hits_at_least_3 == 3
    assert first.hits_at_least_4 == 1
    assert first.draws_evaluated == 3


def test_report_does_not_claim_prediction() -> None:
    rules = _rules()
    prizes = _prizes()
    draws = [Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=7)]
    tickets = [
        [1, 2, 3, 4, 5, 6],
        [8, 9, 10, 11, 12, 13],
        [14, 15, 16, 17, 18, 19],
        [20, 21, 22, 23, 24, 25],
        [26, 27, 28, 29, 30, 31],
        [32, 33, 34, 35, 36, 37],
        [38, 39, 40, 41, 42, 43],
        [44, 45, 46, 47, 48, 49],
    ]
    result = evaluate_system(_system(rules, tickets, "demo"), draws, rules, prizes)
    report = format_evaluation_report(result, "demo").lower()
    assert "does not predict" in report
    assert "historical" in report
