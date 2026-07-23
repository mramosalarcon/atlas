"""Per-number historical appearance profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


@dataclass(frozen=True)
class NumberProfile:
    number: int
    total_main_count: int
    rolling_counts: dict[int, int]
    recency: int | None
    additional_count: int


def compute_number_profiles(
    draws: Sequence[Draw],
    rules: LotteryRules,
    rolling_windows: Sequence[int],
) -> dict[int, NumberProfile]:
    ordered = sorted(draws, key=lambda d: d.contest)
    draw_count = len(ordered)
    windows = tuple(sorted({int(w) for w in rolling_windows if int(w) > 0}))

    total_main = {n: 0 for n in range(rules.min_number, rules.max_number + 1)}
    additional = {n: 0 for n in range(rules.min_number, rules.max_number + 1)}
    last_main_index: dict[int, int | None] = {
        n: None for n in range(rules.min_number, rules.max_number + 1)
    }

    for index, draw in enumerate(ordered):
        for number in draw.mains:
            total_main[number] += 1
            last_main_index[number] = index
        if draw.additional is not None:
            additional[draw.additional] += 1

    rolling_counts: dict[int, dict[int, int]] = {
        n: {w: 0 for w in windows}
        for n in range(rules.min_number, rules.max_number + 1)
    }
    for window in windows:
        recent = ordered[-window:] if draw_count else []
        for draw in recent:
            for number in draw.mains:
                rolling_counts[number][window] += 1

    profiles: dict[int, NumberProfile] = {}
    for number in range(rules.min_number, rules.max_number + 1):
        last_index = last_main_index[number]
        recency = None if last_index is None else (draw_count - 1 - last_index)
        profiles[number] = NumberProfile(
            number=number,
            total_main_count=total_main[number],
            rolling_counts=dict(rolling_counts[number]),
            recency=recency,
            additional_count=additional[number],
        )
    return profiles


def format_number_profile_report(profile: NumberProfile, draws_evaluated: int) -> str:
    rolling = ", ".join(
        f"w{window}={count}" for window, count in sorted(profile.rolling_counts.items())
    )
    recency = "null" if profile.recency is None else str(profile.recency)
    return (
        "ATLAS number profile — historical appearance diagnostics only; "
        "does not predict the next draw.\n"
        f"Number: {profile.number}\n"
        f"Draws in set: {draws_evaluated}\n"
        f"Main appearances: {profile.total_main_count}\n"
        f"Rolling main counts: {rolling}\n"
        f"Recency (contests since last main): {recency}\n"
        f"Additional appearances: {profile.additional_count}\n"
    )
