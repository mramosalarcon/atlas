"""Bootstrap significance tests."""

from __future__ import annotations

from atlas.evaluation.bootstrap import paired_bootstrap_ci


def test_bootstrap_reproducible() -> None:
    deltas = [1, 2, -1, 3, 0]
    first = paired_bootstrap_ci(deltas, n_resamples=200, ci_level=0.95, seed=7)
    second = paired_bootstrap_ci(deltas, n_resamples=200, ci_level=0.95, seed=7)
    assert first == second
    assert first.ci_lower <= first.mean_delta <= first.ci_upper


def test_negative_deltas_ci_below_zero() -> None:
    deltas = [-5, -4, -3, -2, -1]
    result = paired_bootstrap_ci(deltas, n_resamples=300, ci_level=0.95, seed=1)
    assert result.ci_upper < 0
    assert result.ci_lower <= result.mean_delta
