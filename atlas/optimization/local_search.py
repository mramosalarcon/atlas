"""Local search polish seeded from covering optimizer."""

from __future__ import annotations

from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.covering import CoveringOptimizer
from atlas.optimization.pairs import coverage_union, pairs_in_numbers
from atlas.optimization.strategy import OptimizationStrategy


class LocalSearchOptimizer(OptimizationStrategy):
    def __init__(self) -> None:
        self.last_accepts = 0
        self.last_train_metric = 0
        self.last_pairs_covered = 0

    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "local-search",
    ) -> TicketSystem:
        if not settings.local_search.enabled:
            raise ValueError("Local-search optimizer is disabled in config")
        _ = settings.seed  # report parity; neighborhood order is lex-deterministic

        seed_system = CoveringOptimizer().optimize(
            draws, rules, settings, name=f"{name}-seed"
        )
        polished, accepts = hill_climb(
            seed_system,
            draws,
            rules,
            min_hits=settings.local_search.primary_metric_min_hits,
            max_passes=settings.local_search.max_passes,
        )
        result = TicketSystem.create(list(polished.tickets), rules, name=name)
        self.last_accepts = accepts
        self.last_train_metric = primary_metric_count(
            result, draws, min_hits=settings.local_search.primary_metric_min_hits
        )
        self.last_pairs_covered = pair_coverage_count(result)
        return result


def primary_metric_count(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    min_hits: int,
) -> int:
    draw_sets = [frozenset(draw.mains) for draw in draws]
    ticket_sets = [frozenset(ticket.numbers) for ticket in system.tickets]
    count = 0
    for draw_set in draw_sets:
        best = 0
        for ticket_set in ticket_sets:
            hits = len(ticket_set & draw_set)
            if hits > best:
                best = hits
        if best >= min_hits:
            count += 1
    return count


def pair_coverage_count(system: TicketSystem) -> int:
    return len(coverage_union(system.tickets))


def objective_score(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    min_hits: int,
) -> tuple[int, int]:
    return (
        primary_metric_count(system, draws, min_hits=min_hits),
        pair_coverage_count(system),
    )


def apply_replacement(
    system: TicketSystem,
    rules: LotteryRules,
    *,
    ticket_index: int,
    remove: int,
    add: int,
) -> TicketSystem | None:
    current = system.tickets[ticket_index].numbers
    if remove not in current or add in current:
        return None
    replacement = tuple(sorted(n for n in current if n != remove) + [add])
    for idx, ticket in enumerate(system.tickets):
        if idx != ticket_index and ticket.numbers == replacement:
            return None
    try:
        new_ticket = Ticket.create(replacement, rules)
    except Exception:
        return None
    new_tickets = list(system.tickets)
    new_tickets[ticket_index] = new_ticket
    try:
        return TicketSystem.create(new_tickets, rules, name=system.name)
    except Exception:
        return None


def iter_moves(system: TicketSystem, rules: LotteryRules):
    population = range(rules.min_number, rules.max_number + 1)
    for ticket_index, ticket in enumerate(system.tickets):
        for remove in ticket.numbers:
            for add in population:
                if add in ticket.numbers:
                    continue
                yield ticket_index, remove, add


def hill_climb(
    seed: TicketSystem,
    draws: Sequence[Draw],
    rules: LotteryRules,
    *,
    min_hits: int,
    max_passes: int,
) -> tuple[TicketSystem, int]:
    draw_sets = [frozenset(draw.mains) for draw in draws]
    ticket_sets = [frozenset(t.numbers) for t in seed.tickets]
    # hits[draw_idx][ticket_idx]
    hits = [
        [len(ticket_set & draw_set) for ticket_set in ticket_sets]
        for draw_set in draw_sets
    ]
    best_primary = sum(1 for row in hits if max(row) >= min_hits)
    best_pairs = len(coverage_union(seed.tickets))
    current_numbers = [t.numbers for t in seed.tickets]
    accepts = 0

    population = list(range(rules.min_number, rules.max_number + 1))

    for _ in range(max_passes):
        improved = False
        for ticket_index, numbers in enumerate(current_numbers):
            others = {
                nums for idx, nums in enumerate(current_numbers) if idx != ticket_index
            }
            for remove in numbers:
                for add in population:
                    if add in numbers:
                        continue
                    replacement = tuple(
                        sorted(n for n in numbers if n != remove) + [add]
                    )
                    if replacement in others:
                        continue
                    new_set = frozenset(replacement)
                    new_primary = 0
                    for draw_idx, draw_set in enumerate(draw_sets):
                        row = hits[draw_idx]
                        new_hits = len(new_set & draw_set)
                        best = new_hits
                        for idx, value in enumerate(row):
                            if idx == ticket_index:
                                continue
                            if value > best:
                                best = value
                        if best >= min_hits:
                            new_primary += 1

                    if new_primary < best_primary:
                        continue
                    # Pair coverage only when primary does not worsen (and for ties).
                    trial_tickets = list(current_numbers)
                    trial_tickets[ticket_index] = replacement
                    new_pairs = len(
                        set().union(*(pairs_in_numbers(nums) for nums in trial_tickets))
                    )
                    if (new_primary, new_pairs) <= (best_primary, best_pairs):
                        continue

                    # Accept move.
                    current_numbers = trial_tickets
                    ticket_sets[ticket_index] = new_set
                    for draw_idx, draw_set in enumerate(draw_sets):
                        hits[draw_idx][ticket_index] = len(new_set & draw_set)
                    best_primary = new_primary
                    best_pairs = new_pairs
                    accepts += 1
                    improved = True
                    break
                if improved:
                    break
            if improved:
                break
        if not improved:
            break

    tickets = [Ticket.create(nums, rules) for nums in current_numbers]
    return TicketSystem.create(tickets, rules, name=seed.name), accepts


def format_local_search_report(
    system: TicketSystem,
    *,
    seed: int,
    max_passes: int,
    train_contests: tuple[int, int] | None,
    train_metric: int,
    pairs_covered: int,
    accepts: int,
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
        "ATLAS local-search optimize — comparison candidate from historical train search only; "
        "does not predict the next draw and is not auto-accepted.\n"
        f"System: {system.name}\n"
        f"Seed: {seed}\n"
        f"Max passes: {max_passes}\n"
        f"Accepted moves: {accepts}\n"
        f"{contest_line}"
        f"Train primary-metric count: {train_metric}\n"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Tickets:\n{tickets}\n"
    )
