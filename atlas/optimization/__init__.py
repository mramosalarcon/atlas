"""Optimization package."""

from atlas.optimization.greedy import (
    GreedyOptimizer,
    covered_pair_count,
    format_optimize_report,
    generate_candidate_tickets,
)
from atlas.optimization.pairs import (
    coverage_union,
    new_pair_count,
    pairs_in_numbers,
    pairs_in_ticket,
)
from atlas.optimization.strategy import OptimizationStrategy

__all__ = [
    "GreedyOptimizer",
    "OptimizationStrategy",
    "coverage_union",
    "covered_pair_count",
    "format_optimize_report",
    "generate_candidate_tickets",
    "new_pair_count",
    "pairs_in_numbers",
    "pairs_in_ticket",
]
