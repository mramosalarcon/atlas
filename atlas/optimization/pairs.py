"""Unordered pair helpers for coverage-oriented optimization."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from atlas.domain.ticket import Ticket


Pair = tuple[int, int]


def pairs_in_numbers(numbers: Sequence[int]) -> set[Pair]:
    ordered = sorted(numbers)
    return {(left, right) for left, right in combinations(ordered, 2)}


def pairs_in_ticket(ticket: Ticket) -> set[Pair]:
    return pairs_in_numbers(ticket.numbers)


def coverage_union(tickets: Iterable[Ticket]) -> set[Pair]:
    covered: set[Pair] = set()
    for ticket in tickets:
        covered |= pairs_in_ticket(ticket)
    return covered


def new_pair_count(ticket: Ticket, covered: set[Pair]) -> int:
    return len(pairs_in_ticket(ticket) - covered)
