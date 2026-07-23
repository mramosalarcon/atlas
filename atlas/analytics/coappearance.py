"""Main-number pair co-appearance diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


@dataclass(frozen=True)
class PairStat:
    left: int
    right: int
    count: int
    rate: float

    @property
    def pair(self) -> tuple[int, int]:
        return (self.left, self.right)


def compute_coappearance(
    draws: Sequence[Draw],
    rules: LotteryRules,
) -> dict[tuple[int, int], PairStat]:
    if not draws:
        raise ValueError("Cannot compute co-appearance rates with zero draws")

    counts: dict[tuple[int, int], int] = {}
    for draw in draws:
        for left, right in combinations(sorted(draw.mains), 2):
            key = (left, right)
            counts[key] = counts.get(key, 0) + 1

    draw_count = len(draws)
    stats: dict[tuple[int, int], PairStat] = {}
    for left in range(rules.min_number, rules.max_number + 1):
        for right in range(left + 1, rules.max_number + 1):
            count = counts.get((left, right), 0)
            stats[(left, right)] = PairStat(
                left=left,
                right=right,
                count=count,
                rate=count / draw_count,
            )
    return stats


def top_pairs(stats: dict[tuple[int, int], PairStat], n: int) -> list[PairStat]:
    if n < 0:
        raise ValueError("n must be >= 0")
    ordered = sorted(
        stats.values(),
        key=lambda item: (-item.count, item.left, item.right),
    )
    return ordered[:n]


def format_pairs_report(pairs: Sequence[PairStat], draws_evaluated: int) -> str:
    lines = [
        "ATLAS co-appearance pairs — historical diagnostics only; "
        "does not predict the next draw.",
        f"Draws in set: {draws_evaluated}",
        "Top pairs (count, rate):",
    ]
    for pair in pairs:
        lines.append(
            f"  {{{pair.left},{pair.right}}}: count={pair.count} rate={pair.rate:.6f}"
        )
    return "\n".join(lines) + "\n"
