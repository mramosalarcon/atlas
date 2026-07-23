"""Pair coverage helper tests."""

from __future__ import annotations

from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.optimization.pairs import coverage_union, new_pair_count, pairs_in_ticket


def test_pairs_in_ticket_count() -> None:
    rules = LotteryRules(1, 10, 4, True, 8)
    ticket = Ticket.create([1, 2, 3, 4], rules)
    # C(4,2) = 6
    assert len(pairs_in_ticket(ticket)) == 6
    assert (1, 2) in pairs_in_ticket(ticket)
    assert (2, 1) not in pairs_in_ticket(ticket)


def test_new_pair_count_incremental() -> None:
    rules = LotteryRules(1, 10, 3, True, 8)
    first = Ticket.create([1, 2, 3], rules)
    second = Ticket.create([1, 2, 4], rules)
    covered = coverage_union([first])
    # second adds pairs (1,4) and (2,4); (1,2) already covered
    assert new_pair_count(second, covered) == 2
    assert new_pair_count(first, covered) == 0
