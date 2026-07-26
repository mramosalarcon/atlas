"""Ensemble / multi-seed ticket pooling and draft."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.covering import CoveringOptimizer
from atlas.optimization.greedy import GreedyOptimizer
from atlas.optimization.local_search import pair_coverage_count, primary_metric_count
from atlas.optimization.pairs import coverage_union
from atlas.optimization.strategy import OptimizationStrategy


class EnsemblePoolError(ValueError):
    """Raised when the ticket pool cannot support a full system draft."""


def pool_tickets_from_systems(
    systems: Sequence[TicketSystem],
) -> dict[tuple[int, ...], Ticket]:
    pool: dict[tuple[int, ...], Ticket] = {}
    for system in systems:
        for ticket in system.tickets:
            pool[ticket.numbers] = ticket
    return pool


def load_system_file(path: Path, rules: LotteryRules, *, name: str | None = None) -> TicketSystem:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        tickets_raw = payload["tickets"]
        system_name = str(payload.get("name", name or path.stem))
    else:
        tickets_raw = payload
        system_name = name or path.stem
    tickets = [Ticket.create(numbers, rules) for numbers in tickets_raw]
    return TicketSystem.create(tickets, rules, name=system_name)


def pool_tickets_from_files(
    paths: Sequence[Path],
    rules: LotteryRules,
) -> dict[tuple[int, ...], Ticket]:
    systems = [load_system_file(path, rules) for path in paths]
    return pool_tickets_from_systems(systems)


def generate_pool(
    draws: Sequence[Draw],
    rules: LotteryRules,
    settings: OptimizerSettings,
) -> dict[tuple[int, ...], Ticket]:
    ensemble = settings.ensemble
    pool: dict[tuple[int, ...], Ticket] = {}
    for seed in ensemble.seeds:
        seeded = replace(settings, seed=seed)
        for source in ensemble.sources:
            if source == "greedy":
                if not settings.greedy.enabled:
                    raise ValueError("optimizer.greedy.enabled is false")
                system = GreedyOptimizer().optimize(
                    draws, rules, seeded, name=f"greedy-s{seed}"
                )
            elif source == "covering":
                if not settings.covering.enabled:
                    raise ValueError("optimizer.covering.enabled is false")
                system = CoveringOptimizer().optimize(
                    draws, rules, seeded, name=f"covering-s{seed}"
                )
            else:
                raise ValueError(f"unsupported ensemble source: {source!r}")
            for ticket in system.tickets:
                pool[ticket.numbers] = ticket
    return pool


def primary_metric_for_tickets(
    tickets: Sequence[Ticket],
    draws: Sequence[Draw],
    *,
    min_hits: int,
) -> int:
    draw_sets = [frozenset(draw.mains) for draw in draws]
    ticket_sets = [frozenset(ticket.numbers) for ticket in tickets]
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


def draft_from_pool(
    pool: dict[tuple[int, ...], Ticket],
    draws: Sequence[Draw],
    rules: LotteryRules,
    *,
    min_hits: int,
) -> list[Ticket]:
    if len(pool) < rules.system_size:
        raise EnsemblePoolError(
            f"ensemble pool has {len(pool)} unique tickets; "
            f"need at least {rules.system_size}"
        )
    selected: list[Ticket] = []
    remaining = dict(pool)
    while len(selected) < rules.system_size:
        best_key: tuple[int, ...] | None = None
        best_primary = -1
        best_pairs = -1
        for key, ticket in remaining.items():
            trial = selected + [ticket]
            primary = primary_metric_for_tickets(trial, draws, min_hits=min_hits)
            pairs = len(coverage_union(trial))
            if (
                best_key is None
                or primary > best_primary
                or (primary == best_primary and pairs > best_pairs)
                or (
                    primary == best_primary
                    and pairs == best_pairs
                    and key < best_key
                )
            ):
                best_key = key
                best_primary = primary
                best_pairs = pairs
        assert best_key is not None
        selected.append(remaining.pop(best_key))
    return selected


class EnsembleOptimizer(OptimizationStrategy):
    def __init__(self) -> None:
        self.last_pool_size = 0
        self.last_train_metric = 0
        self.last_pairs_covered = 0
        self.last_seeds: tuple[int, ...] = ()
        self.last_sources: tuple[str, ...] = ()

    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "ensemble",
        extra_pool: dict[tuple[int, ...], Ticket] | None = None,
    ) -> TicketSystem:
        if not settings.ensemble.enabled:
            raise ValueError("Ensemble optimizer is disabled in config")
        pool = generate_pool(draws, rules, settings)
        if extra_pool:
            pool.update(extra_pool)
        self.last_pool_size = len(pool)
        self.last_seeds = settings.ensemble.seeds
        self.last_sources = settings.ensemble.sources
        tickets = draft_from_pool(
            pool,
            draws,
            rules,
            min_hits=settings.ensemble.primary_metric_min_hits,
        )
        result = TicketSystem.create(tickets, rules, name=name)
        self.last_train_metric = primary_metric_count(
            result,
            draws,
            min_hits=settings.ensemble.primary_metric_min_hits,
        )
        self.last_pairs_covered = pair_coverage_count(result)
        return result


def format_ensemble_report(
    system: TicketSystem,
    *,
    seeds: Sequence[int],
    sources: Sequence[str],
    pool_size: int,
    train_contests: tuple[int, int] | None,
    train_metric: int,
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
        "ATLAS ensemble optimize — comparison candidate from historical train search "
        "only; does not predict the next draw and is not auto-accepted.\n"
        f"System: {system.name}\n"
        f"Seeds: {list(seeds)}\n"
        f"Sources: {list(sources)}\n"
        f"Unique tickets pooled: {pool_size}\n"
        f"{contest_line}"
        f"Train primary-metric draws: {train_metric}\n"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Tickets:\n{tickets}\n"
    )
