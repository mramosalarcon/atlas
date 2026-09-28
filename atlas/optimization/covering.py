"""Covering-design optimizer by constructive multi-order tuple priority."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

from atlas.config.settings import CoveringOptimizerSettings, OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.pairs import (
    coverage_count_k,
    coverage_union,
)
from atlas.optimization.strategy import OptimizationStrategy

Pair = tuple[int, int]
TupleKey = tuple[int, ...]

# Materialize full uniform maps only when C(n,k) stays under this threshold.
_UNIFORM_EAGER_LIMIT = 50_000


@dataclass
class UncoveredState:
    orders: tuple[int, ...]
    maps: dict[int, dict[TupleKey, float]]
    order_weights: dict[int, float]
    population: tuple[int, ...]
    lazy_uniform: set[int] = field(default_factory=set)
    covered_lazy: dict[int, set[TupleKey]] = field(default_factory=dict)

    def effective_weight(self, k: int, key: TupleKey) -> float:
        if key in self.maps.get(k, {}):
            return self.maps[k][key]
        if k in self.lazy_uniform and key not in self.covered_lazy.get(k, set()):
            return self.order_weights[k]
        return 0.0

    def remove_ticket_tuples(self, numbers: Sequence[int]) -> None:
        ordered = sorted(numbers)
        for k in self.orders:
            for key in combinations(ordered, k):
                self.maps.get(k, {}).pop(key, None)
                if k in self.lazy_uniform:
                    self.covered_lazy.setdefault(k, set()).add(key)


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

        state = build_uncovered_state(draws, rules, settings.covering)
        _ = settings.seed

        selected: list[Ticket] = []
        for _ in range(rules.system_size):
            ticket = construct_ticket(state, rules)
            selected.append(ticket)
            state.remove_ticket_tuples(ticket.numbers)

        return TicketSystem.create(selected, rules, name=name)


def build_pair_weights(
    draws: Sequence[Draw],
    rules: LotteryRules,
    *,
    pair_weight: str,
) -> dict[Pair, float]:
    """Legacy pair-only weight map (used by unit tests and pair helpers)."""
    covering = CoveringOptimizerSettings(
        enabled=True,
        pair_weight=pair_weight,
        cover_orders=(2,),
        order_weights=((2, 1.0),),
    )
    state = build_uncovered_state(draws, rules, covering)
    return state.maps[2]  # type: ignore[return-value]


def build_uncovered_state(
    draws: Sequence[Draw],
    rules: LotteryRules,
    covering: CoveringOptimizerSettings,
) -> UncoveredState:
    mode = covering.pair_weight
    if mode not in {"train_frequency", "uniform"}:
        raise ValueError(f"Unsupported pair_weight: {mode!r}")

    orders = covering.cover_orders
    order_weights = covering.order_weight_map()
    population = tuple(range(rules.min_number, rules.max_number + 1))
    n = len(population)
    maps: dict[int, dict[TupleKey, float]] = {}
    lazy_uniform: set[int] = set()
    covered_lazy: dict[int, set[TupleKey]] = {}

    for k in orders:
        ow = order_weights[k]
        universe_size = _combination_count(n, k)
        if mode == "uniform" and universe_size > _UNIFORM_EAGER_LIMIT:
            maps[k] = {}
            lazy_uniform.add(k)
            covered_lazy[k] = set()
            continue

        weights: dict[TupleKey, float] = {}
        if mode == "uniform":
            for key in combinations(population, k):
                weights[key] = ow
        else:
            counts: dict[TupleKey, int] = defaultdict(int)
            for draw in draws:
                for key in combinations(sorted(draw.mains), k):
                    counts[key] += 1
            if k == 2:
                for key in combinations(population, k):
                    weights[key] = ow * float(counts.get(key, 0))
            else:
                for key, count in counts.items():
                    weights[key] = ow * float(count)
        maps[k] = weights

    return UncoveredState(
        orders=orders,
        maps=maps,
        order_weights={k: order_weights[k] for k in orders},
        population=population,
        lazy_uniform=lazy_uniform,
        covered_lazy=covered_lazy,
    )


def best_pair(uncovered: dict[Pair, float]) -> Pair:
    if not uncovered:
        raise ValueError("No uncovered pairs remain")
    return min(uncovered.keys(), key=lambda pair: (-uncovered[pair], pair))


def best_seed_tuple(state: UncoveredState) -> TupleKey:
    best: TupleKey | None = None
    best_weight = float("-inf")
    best_k = -1

    for k, amap in state.maps.items():
        for key, weight in amap.items():
            if (
                weight > best_weight
                or (weight == best_weight and k > best_k)
                or (weight == best_weight and k == best_k and (best is None or key < best))
            ):
                best = key
                best_weight = weight
                best_k = k

    for k in sorted(state.lazy_uniform, reverse=True):
        weight = state.order_weights[k]
        if weight < best_weight:
            continue
        for key in combinations(state.population, k):
            if key in state.covered_lazy.get(k, set()):
                continue
            if (
                weight > best_weight
                or (weight == best_weight and k > best_k)
                or (
                    weight == best_weight
                    and k == best_k
                    and (best is None or key < best)
                )
            ):
                best = key
                best_weight = weight
                best_k = k
            # first uncovered lex key is enough when weights equal within this k
            if weight == best_weight and k == best_k and best == key:
                break
        if best is not None and best_weight == weight and best_k == k:
            break

    if best is None:
        raise ValueError("No uncovered tuples remain")
    return best


def construct_ticket(
    uncovered: UncoveredState | dict[Pair, float],
    rules: LotteryRules,
) -> Ticket:
    if isinstance(uncovered, dict):
        state = UncoveredState(
            orders=(2,),
            maps={2: dict(uncovered)},
            order_weights={2: 1.0},
            population=tuple(range(rules.min_number, rules.max_number + 1)),
        )
    else:
        state = uncovered

    numbers: set[int] = set()
    population = list(state.population)

    while len(numbers) < rules.main_count:
        if not numbers:
            try:
                seed = best_seed_tuple(state)
            except ValueError:
                _fill_remaining(numbers, population, rules.main_count)
                break
            numbers.update(seed)
            if len(numbers) > rules.main_count:
                numbers = set(sorted(numbers)[: rules.main_count])
            continue

        best_number = _best_extension(numbers, state, population)
        if best_number is None:
            _fill_remaining(numbers, population, rules.main_count)
            break
        # If every extension scores 0, still take the lex-best from _best_extension
        numbers.add(best_number)

    if len(numbers) < rules.main_count:
        _fill_remaining(numbers, population, rules.main_count)

    return Ticket.create(sorted(numbers)[: rules.main_count], rules)


def _best_extension(
    numbers: set[int],
    state: UncoveredState,
    population: list[int],
) -> int | None:
    best_number: int | None = None
    best_score: float | None = None
    for candidate in population:
        if candidate in numbers:
            continue
        score = _extension_score(numbers, candidate, state)
        if best_score is None or score > best_score:
            best_score = score
            best_number = candidate
        elif score == best_score and best_number is not None and candidate < best_number:
            best_number = candidate
    return best_number


def _extension_score(numbers: set[int], candidate: int, state: UncoveredState) -> float:
    trial = numbers | {candidate}
    score = 0.0
    for k in state.orders:
        if len(trial) < k:
            continue
        for key in combinations(sorted(trial), k):
            if candidate not in key:
                continue
            score += state.effective_weight(k, key)
    return score


def _fill_remaining(numbers: set[int], population: list[int], main_count: int) -> None:
    for number in population:
        if number not in numbers:
            numbers.add(number)
        if len(numbers) >= main_count:
            return


def _combination_count(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


def format_covering_report(
    system: TicketSystem,
    *,
    seed: int,
    pair_weight: str,
    train_contests: tuple[int, int] | None,
    pairs_covered: int,
    triples_covered: int = 0,
    quads_covered: int = 0,
    cover_orders: Sequence[int] | None = None,
) -> str:
    contest_line = (
        f"Train contests used for search: {train_contests[0]}–{train_contests[1]}\n"
        if train_contests
        else ""
    )
    orders_line = (
        f"Cover orders: {list(cover_orders)}\n" if cover_orders is not None else ""
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
        f"{orders_line}"
        f"{contest_line}"
        f"Unordered pairs covered: {pairs_covered}\n"
        f"Unordered triples covered: {triples_covered}\n"
        f"Unordered quads covered: {quads_covered}\n"
        f"Tickets:\n{tickets}\n"
    )


def covered_pair_count(system: TicketSystem) -> int:
    return len(coverage_union(system.tickets))


def covered_triple_count(system: TicketSystem) -> int:
    return coverage_count_k(system.tickets, 3)


def covered_quad_count(system: TicketSystem) -> int:
    return coverage_count_k(system.tickets, 4)
