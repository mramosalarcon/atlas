"""Chronological train/validation split helpers."""

from __future__ import annotations

from typing import Sequence

from atlas.domain.draw import Draw


def split_train_validation(
    draws: Sequence[Draw],
    validation_ratio: float,
) -> tuple[list[Draw], list[Draw]]:
    if not 0.0 < validation_ratio < 1.0:
        raise ValueError("validation_ratio must be between 0 and 1 (exclusive)")
    ordered = sorted(draws, key=lambda d: d.contest)
    if not ordered:
        return [], []
    validation_count = max(1, int(round(len(ordered) * validation_ratio)))
    if validation_count >= len(ordered):
        validation_count = len(ordered) - 1
    split_index = len(ordered) - validation_count
    return list(ordered[:split_index]), list(ordered[split_index:])
