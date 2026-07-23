"""Seeded paired bootstrap over fold deltas."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class BootstrapResult:
    mean_delta: float
    ci_lower: float
    ci_upper: float
    n_resamples: int
    ci_level: float
    seed: int


def paired_bootstrap_ci(
    deltas: Sequence[float | int],
    *,
    n_resamples: int,
    ci_level: float,
    seed: int,
) -> BootstrapResult:
    if not deltas:
        raise ValueError("Cannot bootstrap empty delta list")
    if n_resamples < 1:
        raise ValueError("n_resamples must be >= 1")
    if not 0.0 < ci_level < 1.0:
        raise ValueError("ci_level must be between 0 and 1")

    values = [float(d) for d in deltas]
    rng = random.Random(seed)
    means: list[float] = []
    n = len(values)
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)

    means.sort()
    alpha = 1.0 - ci_level
    lower_idx = int(alpha / 2.0 * (n_resamples - 1))
    upper_idx = int((1.0 - alpha / 2.0) * (n_resamples - 1))
    lower_idx = max(0, min(lower_idx, n_resamples - 1))
    upper_idx = max(0, min(upper_idx, n_resamples - 1))

    return BootstrapResult(
        mean_delta=sum(values) / n,
        ci_lower=means[lower_idx],
        ci_upper=means[upper_idx],
        n_resamples=n_resamples,
        ci_level=ci_level,
        seed=seed,
    )
