"""Deterministic greedy optimizer by incremental pair coverage."""

from __future__ import annotations

import random
from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.pairs import coverage_union, new_pair_count, pairs_in_ticket
from atlas.optimization.strategy import OptimizationStrategy


class GreedyOptimizer(OptimizationStrategy):
    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "greedy",
    ) -> TicketSystem:
        if not settings.greedy.enabled:
            raise ValueError("Greedy optimizer is disabled in config")

        # draws are accepted for the train-only contract; pair-coverage greedy
        # does not score hits against them during search.
        _ = draws

        selected: list[Ticket] = []
        covered: set[tuple[int, int]] = set()
        rng = random.Random(settings.seed)

        for slot in range(rules.system_size):
            candidates = generate_candidate_tickets(
                rules,
                pool_size=settings.candidate_pool_size,
                rng=rng,
                exclude={t.numbers for t in selected},
            )
            if not candidates:
                raise RuntimeError(
                    f"Greedy optimizer could not generate candidates for slot {slot + 1}"
                )
            best = _select_best_candidate(candidates, covered)
            selected.append(best)
            covered |= pairs_in_ticket(best)

        return TicketSystem.create(selected, rules, name=name)


def generate_candidate_tickets(
    rules: LotteryRules,
    *,
    pool_size: int,
    rng: random.Random,
    exclude: set[tuple[int, ...]] | None = None,
) -> list[Ticket]:
    if pool_size < 1:
        raise ValueError("candidate_pool_size must be >= 1")
    excluded = exclude or set()
    population = list(range(rules.min_number, rules.max_number + 1))
    if len(population) < rules.main_count:
        raise ValueError("Number range smaller than main_count")

    unique: dict[tuple[int, ...], Ticket] = {}
    # Bounded attempts to fill the pool with distinct tickets.
    max_attempts = max(pool_size * 20, pool_size)
    attempts = 0
    while len(unique) < pool_size and attempts < max_attempts:
        attempts += 1
        picks = tuple(sorted(rng.sample(population, rules.main_count)))
        if picks in excluded or picks in unique:
            continue
        unique[picks] = Ticket.create(picks, rules)
    return list(unique.values())


def _select_best_candidate(
    candidates: Sequence[Ticket],
    covered: set[tuple[int, int]],
) -> Ticket:
    def sort_key(ticket: Ticket) -> tuple[int, tuple[int, ...]]:
        # Maximize new pairs; tie-break by ascending ticket numbers.
        return (-new_pair_count(ticket, covered), ticket.numbers)

    return sorted(candidates, key=sort_key)[0]


def format_optimize_report(
    system: TicketSystem,
    *,
    seed: int,
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
        "ATLAS greedy optimize — comparison candidate from historical train search only; "
        "does not predict the next draw and is not auto-accepted.\n"
        f"System: {system.name}\n"
        f"Seed: {seed}\n"
        f"{contest_line}"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Tickets:\n{tickets}\n"
    )


def covered_pair_count(system: TicketSystem) -> int:
    return len(coverage_union(system.tickets))
