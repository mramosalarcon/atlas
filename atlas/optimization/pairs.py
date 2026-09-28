"""Unordered k-tuple helpers for coverage-oriented optimization."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from atlas.domain.ticket import Ticket

Pair = tuple[int, int]
TupleKey = tuple[int, ...]


def pairs_in_numbers(numbers: Sequence[int]) -> set[Pair]:
    return tuples_in_numbers(numbers, 2)  # type: ignore[return-value]


def pairs_in_ticket(ticket: Ticket) -> set[Pair]:
    return pairs_in_numbers(ticket.numbers)


def coverage_union(tickets: Iterable[Ticket]) -> set[Pair]:
    return coverage_union_k(tickets, 2)  # type: ignore[return-value]


def new_pair_count(ticket: Ticket, covered: set[Pair]) -> int:
    return len(pairs_in_ticket(ticket) - covered)


def tuples_in_numbers(numbers: Sequence[int], k: int) -> set[TupleKey]:
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    ordered = sorted(numbers)
    if len(ordered) < k:
        return set()
    return {tuple(combo) for combo in combinations(ordered, k)}


def tuples_in_ticket(ticket: Ticket, k: int) -> set[TupleKey]:
    return tuples_in_numbers(ticket.numbers, k)


def coverage_union_k(tickets: Iterable[Ticket], k: int) -> set[TupleKey]:
    covered: set[TupleKey] = set()
    for ticket in tickets:
        covered |= tuples_in_ticket(ticket, k)
    return covered


def coverage_count_k(tickets: Iterable[Ticket], k: int) -> int:
    return len(coverage_union_k(tickets, k))
