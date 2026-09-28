"""Deterministic Atlas Score (atlas-score-v1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.config.settings import ScoreWeightSettings
from atlas.domain.draw import Draw
from atlas.domain.ticket_system import TicketSystem
from atlas.optimization.local_search import primary_metric_count
from atlas.optimization.pairs import coverage_count_k, coverage_union

FORMULA_VERSION = "atlas-score-v1"


@dataclass(frozen=True)
class AtlasScoreResult:
    score: float
    primary: int
    pairs: int
    triples: int
    quads: int
    weights: ScoreWeightSettings
    formula_version: str = FORMULA_VERSION


def compute_atlas_score(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    weights: ScoreWeightSettings,
    min_hits: int,
) -> AtlasScoreResult:
    primary = primary_metric_count(system, draws, min_hits=min_hits)
    pairs = len(coverage_union(system.tickets))
    triples = coverage_count_k(system.tickets, 3)
    quads = coverage_count_k(system.tickets, 4)
    score = (
        weights.primary * primary
        + weights.pairs * pairs
        + weights.triples * triples
        + weights.quads * quads
    )
    return AtlasScoreResult(
        score=score,
        primary=primary,
        pairs=pairs,
        triples=triples,
        quads=quads,
        weights=weights,
    )


def format_score_report(
    result: AtlasScoreResult,
    *,
    system_name: str,
    window: str,
    contest_range: tuple[int, int] | None,
) -> str:
    contests = (
        f"Contests: {contest_range[0]}–{contest_range[1]}\n" if contest_range else ""
    )
    return (
        "ATLAS Score — historical diagnostic ranking only; does not predict the next "
        "draw and does not auto-promote a champion.\n"
        f"System: {system_name}\n"
        f"Window: {window}\n"
        f"{contests}"
        f"Formula: {result.formula_version}\n"
        f"Score: {result.score:.4f}\n"
        f"Components: primary={result.primary} pairs={result.pairs} "
        f"triples={result.triples} quads={result.quads}\n"
        f"Weights: primary={result.weights.primary} pairs={result.weights.pairs} "
        f"triples={result.weights.triples} quads={result.weights.quads}\n"
    )
