"""Draw entity representing one lottery contest result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from atlas.domain.exceptions import (
    DuplicateNumberError,
    InvalidDrawError,
    InvalidLotteryNumberError,
)
from atlas.domain.lottery_rules import LotteryRules


@dataclass(frozen=True)
class Draw:
    contest: int
    mains: tuple[int, ...]
    additional: int | None
    draw_date: date | None = None
    jackpot: float | None = None

    @classmethod
    def create(
        cls,
        contest: int,
        mains: Sequence[int],
        rules: LotteryRules,
        *,
        additional: int | None = None,
        draw_date: date | None = None,
        jackpot: float | None = None,
        require_sorted: bool = True,
    ) -> Draw:
        if contest < 1:
            raise InvalidDrawError(f"Contest id must be >= 1, got {contest}")

        numbers = tuple(int(n) for n in mains)
        if len(numbers) != rules.main_count:
            raise InvalidDrawError(
                f"Contest {contest}: expected {rules.main_count} main numbers, got {len(numbers)}"
            )
        if len(set(numbers)) != len(numbers):
            raise DuplicateNumberError(f"Contest {contest}: duplicate main numbers in {numbers}")
        for number in numbers:
            if not rules.is_in_range(number):
                raise InvalidLotteryNumberError(
                    f"Contest {contest}: number {number} outside "
                    f"[{rules.min_number}, {rules.max_number}]"
                )
        if require_sorted and numbers != tuple(sorted(numbers)):
            raise InvalidDrawError(f"Contest {contest}: main numbers not ascending: {numbers}")

        resolved_additional: int | None = None
        if rules.has_additional:
            if additional is None:
                raise InvalidDrawError(f"Contest {contest}: additional number is required")
            resolved_additional = int(additional)
            if not rules.is_in_range(resolved_additional):
                raise InvalidLotteryNumberError(
                    f"Contest {contest}: additional number {resolved_additional} outside "
                    f"[{rules.min_number}, {rules.max_number}]"
                )
        elif additional is not None:
            raise InvalidDrawError(f"Contest {contest}: additional number not allowed by rules")

        return cls(
            contest=contest,
            mains=numbers,
            additional=resolved_additional,
            draw_date=draw_date,
            jackpot=jackpot,
        )
