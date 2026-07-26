"""Optimization package."""

from atlas.optimization.covering import CoveringOptimizer, format_covering_report
from atlas.optimization.ensemble import (
    EnsembleOptimizer,
    EnsemblePoolError,
    format_ensemble_report,
)
from atlas.optimization.greedy import (
    GreedyOptimizer,
    covered_pair_count,
    format_optimize_report,
    generate_candidate_tickets,
)
from atlas.optimization.local_search import (
    LocalSearchOptimizer,
    format_local_search_report,
)
from atlas.optimization.pairs import (
    coverage_union,
    new_pair_count,
    pairs_in_numbers,
    pairs_in_ticket,
)
from atlas.optimization.strategy import OptimizationStrategy

__all__ = [
    "CoveringOptimizer",
    "EnsembleOptimizer",
    "EnsemblePoolError",
    "GreedyOptimizer",
    "LocalSearchOptimizer",
    "OptimizationStrategy",
    "coverage_union",
    "covered_pair_count",
    "format_covering_report",
    "format_ensemble_report",
    "format_local_search_report",
    "format_optimize_report",
    "generate_candidate_tickets",
    "new_pair_count",
    "pairs_in_numbers",
    "pairs_in_ticket",
]
