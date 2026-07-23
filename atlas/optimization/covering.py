"""Covering-design optimizer by constructive pair priority."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.pairs import coverage_union, pairs_in_ticket
from atlas.optimization.strategy import OptimizationStrategy

Pair = tuple[int, int]


class CoveringOptimizer(OptimizationStrategy):
    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "covering",
    ) -> TicketSystem:
        if not settings.covering.enabled:
            raise ValueError("Covering optimizer is disabled in config")

        uncovered = build_pair_weights(
            draws,
            rules,
            pair_weight=settings.covering.pair_weight,
        )
        # seed reserved for future residual randomness; construction is lex-deterministic
        _ = settings.seed

        selected: list[Ticket] = []
        for _ in range(rules.system_size):
            ticket = construct_ticket(uncovered, rules)
            selected.append(ticket)
            for pair in pairs_in_ticket(ticket):
                uncovered.pop(pair, None)

        return TicketSystem.create(selected, rules, name=name)


def build_pair_weights(
    draws: Sequence[Draw],
    rules: LotteryRules,
    *,
    pair_weight: str,
) -> dict[Pair, float]:
    if pair_weight not in {"train_frequency", "uniform"}:
        raise ValueError(f"Unsupported pair_weight: {pair_weight!r}")

    weights: dict[Pair, float] = {}
    for left, right in combinations(
        range(rules.min_number, rules.max_number + 1), 2
    ):
        weights[(left, right)] = 0.0

    if pair_weight == "uniform":
        for pair in weights:
            weights[pair] = 1.0
        return weights

    counts: dict[Pair, int] = defaultdict(int)
    for draw in draws:
        for left, right in combinations(sorted(draw.mains), 2):
            counts[(left, right)] += 1
    for pair, count in counts.items():
        if pair in weights:
            weights[pair] = float(count)
    return weights


def best_pair(uncovered: dict[Pair, float]) -> Pair:
    if not uncovered:
        raise ValueError("No uncovered pairs remain")
    return min(uncovered.keys(), key=lambda pair: (-uncovered[pair], pair))


def construct_ticket(
    uncovered: dict[Pair, float],
    rules: LotteryRules,
) -> Ticket:
    numbers: set[int] = set()
    population = list(range(rules.min_number, rules.max_number + 1))

    while len(numbers) < rules.main_count:
        actionable = {
            pair: weight
            for pair, weight in uncovered.items()
            if not (pair[0] in numbers and pair[1] in numbers)
        }
        if not actionable:
            best_number = _best_extension(numbers, uncovered, population)
            if best_number is None:
                _fill_remaining(numbers, population, rules.main_count)
                break
            numbers.add(best_number)
            continue

        top = best_pair(actionable)
        left, right = top
        if not numbers:
            numbers.add(left)
            numbers.add(right)
            continue

        if (left in numbers) ^ (right in numbers):
            numbers.add(right if left in numbers else left)
            continue

        best_number = _best_extension(numbers, actionable, population)
        if best_number is None:
            _fill_remaining(numbers, population, rules.main_count)
            break
        numbers.add(best_number)

    if len(numbers) < rules.main_count:
        _fill_remaining(numbers, population, rules.main_count)

    return Ticket.create(sorted(numbers)[: rules.main_count], rules)


def _best_extension(
    numbers: set[int],
    uncovered: dict[Pair, float],
    population: list[int],
) -> int | None:
    best_number: int | None = None
    best_score: float | None = None
    for candidate in population:
        if candidate in numbers:
            continue
        score = sum(
            uncovered.get((min(candidate, existing), max(candidate, existing)), 0.0)
            for existing in numbers
        )
        if best_score is None or score > best_score:
            best_score = score
            best_number = candidate
        elif score == best_score and best_number is not None and candidate < best_number:
            best_number = candidate
    return best_number


def _fill_remaining(numbers: set[int], population: list[int], main_count: int) -> None:
    for number in population:
        if number not in numbers:
            numbers.add(number)
        if len(numbers) >= main_count:
            return


def format_covering_report(
    system: TicketSystem,
    *,
    seed: int,
    pair_weight: str,
    train_contests: tuple[int, int] | None,
    pairs_covered: int,
) -> str:
    contest_line = (
        f"Train contests used for search: {train_contests[0]}–{train_contests[1]}\n"
        if train_contests
        else ""
    )
    tickets = "\n".join(
        f"  {idx + 1}: {list(ticket.numbers)}"
        for idx, ticket in enumerate(system.tickets)
    )
    return (
        "ATLAS covering optimize — comparison candidate from historical train search only; "
        "does not predict the next draw and is not auto-accepted.\n"
        f"System: {system.name}\n"
        f"Seed: {seed}\n"
        f"Pair weight: {pair_weight}\n"
        f"{contest_line}"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Tickets:\n{tickets}\n"
    )


def covered_pair_count(system: TicketSystem) -> int:
    return len(coverage_union(system.tickets))
