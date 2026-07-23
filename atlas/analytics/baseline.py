"""Descriptive draw-shape baseline statistics."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Sequence

from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


@dataclass(frozen=True)
class DrawBaseline:
    draws_evaluated: int
    sum_min: float
    sum_max: float
    sum_mean: float
    sum_median: float
    mean_odd_count: float
    decade_occupancy_means: dict[str, float]
    consecutive_pair_fraction: float


def compute_draw_baseline(draws: Sequence[Draw], rules: LotteryRules) -> DrawBaseline:
    if not draws:
        raise ValueError("Cannot compute baseline with zero draws")

    sums = [sum(draw.mains) for draw in draws]
    odd_counts = [sum(1 for n in draw.mains if n % 2 == 1) for draw in draws]
    decades = _decade_labels(rules.min_number, rules.max_number)
    decade_totals = {label: 0.0 for label in decades}
    consecutive_hits = 0

    for draw in draws:
        if _has_consecutive_pair(draw.mains):
            consecutive_hits += 1
        for number in draw.mains:
            decade_totals[_decade_label(number)] += 1

    draw_count = len(draws)
    decade_means = {
        label: decade_totals[label] / draw_count for label in decades
    }

    return DrawBaseline(
        draws_evaluated=draw_count,
        sum_min=float(min(sums)),
        sum_max=float(max(sums)),
        sum_mean=float(mean(sums)),
        sum_median=float(median(sums)),
        mean_odd_count=float(mean(odd_counts)),
        decade_occupancy_means=decade_means,
        consecutive_pair_fraction=consecutive_hits / draw_count,
    )


def format_baseline_report(baseline: DrawBaseline) -> str:
    decades = ", ".join(
        f"{label}={value:.3f}"
        for label, value in baseline.decade_occupancy_means.items()
    )
    return (
        "ATLAS draw baseline — historical reference descriptors under game rules; "
        "does not predict the next draw.\n"
        f"Draws evaluated: {baseline.draws_evaluated}\n"
        f"Sum min/max/mean/median: "
        f"{baseline.sum_min:.1f}/{baseline.sum_max:.1f}/"
        f"{baseline.sum_mean:.3f}/{baseline.sum_median:.3f}\n"
        f"Mean odd main count: {baseline.mean_odd_count:.3f}\n"
        f"Mean decade occupancy: {decades}\n"
        f"Fraction with consecutive pair: {baseline.consecutive_pair_fraction:.4f}\n"
    )


def _has_consecutive_pair(mains: Sequence[int]) -> bool:
    ordered = sorted(mains)
    return any(right - left == 1 for left, right in zip(ordered, ordered[1:]))


def _decade_label(number: int) -> str:
    low = ((number - 1) // 10) * 10 + 1
    high = low + 9
    return f"{low}-{high}"


def _decade_labels(min_number: int, max_number: int) -> list[str]:
    labels: list[str] = []
    start = ((min_number - 1) // 10) * 10 + 1
    while start <= max_number:
        labels.append(f"{start}-{start + 9}")
        start += 10
    return labels
