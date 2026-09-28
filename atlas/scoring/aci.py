"""Bootstrap Atlas Confidence Intervals around Atlas Score."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from atlas.config.settings import AciSettings, ScoreWeightSettings
from atlas.domain.draw import Draw
from atlas.domain.ticket_system import TicketSystem
from atlas.scoring.score import compute_atlas_score




@dataclass(frozen=True)
class AciResult:
    point_score: float
    mean_score: float
    ci_lower: float
    ci_upper: float
    n_resamples: int
    ci_level: float
    seed: int
    pairwise: bool = False


def compute_aci(
    system: TicketSystem,
    draws: Sequence[Draw],
    *,
    weights: ScoreWeightSettings,
    min_hits: int,
    aci: AciSettings,
) -> AciResult:
    if not draws:
        raise ValueError("Cannot compute ACI on empty draw set")
    point = compute_atlas_score(system, draws, weights=weights, min_hits=min_hits)
    samples = _resample_scores(
        [system],
        draws,
        weights=weights,
        min_hits=min_hits,
        aci=aci,
        mode="single",
    )
    return _interval_from_samples(point.score, samples, aci, pairwise=False)


def compute_pairwise_aci(
    baseline: TicketSystem,
    candidate: TicketSystem,
    draws: Sequence[Draw],
    *,
    weights: ScoreWeightSettings,
    min_hits: int,
    aci: AciSettings,
) -> AciResult:
    if not draws:
        raise ValueError("Cannot compute pairwise ACI on empty draw set")
    base = compute_atlas_score(baseline, draws, weights=weights, min_hits=min_hits)
    cand = compute_atlas_score(candidate, draws, weights=weights, min_hits=min_hits)
    point_delta = cand.score - base.score
    samples = _resample_scores(
        [baseline, candidate],
        draws,
        weights=weights,
        min_hits=min_hits,
        aci=aci,
        mode="delta",
    )
    return _interval_from_samples(point_delta, samples, aci, pairwise=True)


def _resample_scores(
    systems: Sequence[TicketSystem],
    draws: Sequence[Draw],
    *,
    weights: ScoreWeightSettings,
    min_hits: int,
    aci: AciSettings,
    mode: str,
) -> list[float]:
    rng = random.Random(aci.seed)
    n = len(draws)
    samples: list[float] = []
    for _ in range(aci.n_resamples):
        indices = [rng.randrange(n) for _ in range(n)]
        resampled = [draws[i] for i in indices]
        if mode == "single":
            result = compute_atlas_score(
                systems[0], resampled, weights=weights, min_hits=min_hits
            )
            samples.append(result.score)
        else:
            base = compute_atlas_score(
                systems[0], resampled, weights=weights, min_hits=min_hits
            )
            cand = compute_atlas_score(
                systems[1], resampled, weights=weights, min_hits=min_hits
            )
            samples.append(cand.score - base.score)
    return samples


def _interval_from_samples(
    point: float,
    samples: list[float],
    aci: AciSettings,
    *,
    pairwise: bool,
) -> AciResult:
    ordered = sorted(samples)
    n_resamples = len(ordered)
    alpha = 1.0 - aci.ci_level
    lower_idx = int(alpha / 2.0 * (n_resamples - 1))
    upper_idx = int((1.0 - alpha / 2.0) * (n_resamples - 1))
    lower_idx = max(0, min(lower_idx, n_resamples - 1))
    upper_idx = max(0, min(upper_idx, n_resamples - 1))
    return AciResult(
        point_score=point,
        mean_score=sum(samples) / n_resamples,
        ci_lower=ordered[lower_idx],
        ci_upper=ordered[upper_idx],
        n_resamples=aci.n_resamples,
        ci_level=aci.ci_level,
        seed=aci.seed,
        pairwise=pairwise,
    )


def format_aci_report(
    result: AciResult,
    *,
    system_name: str,
    baseline_name: str | None = None,
    window: str = "holdout",
) -> str:
    label = (
        f"delta ({system_name} - {baseline_name})"
        if result.pairwise and baseline_name
        else system_name
    )
    return (
        "ATLAS ACI — historical diagnostic uncertainty around Atlas Score; "
        "does not decide promotion and does not predict the next draw.\n"
        f"Target: {label}\n"
        f"Window: {window}\n"
        f"Point: {result.point_score:.4f}\n"
        f"Mean (resamples): {result.mean_score:.4f}\n"
        f"ACI [{result.ci_level:.2f}]: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]\n"
        f"Resamples: {result.n_resamples} seed={result.seed}\n"
    )
