"""Ticket entity and hit evaluation against a draw."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.domain.draw import Draw
from atlas.domain.exceptions import (
    DuplicateNumberError,
    InvalidLotteryNumberError,
    InvalidTicketError,
)
from atlas.domain.lottery_rules import LotteryRules


@dataclass(frozen=True)
class HitResult:
    hits: int
    additional_match: bool


@dataclass(frozen=True)
class Ticket:
    numbers: tuple[int, ...]

    @classmethod
    def create(cls, numbers: Sequence[int], rules: LotteryRules) -> Ticket:
        values = tuple(int(n) for n in numbers)
        if len(values) != rules.main_count:
            raise InvalidTicketError(
                f"Ticket must have {rules.main_count} numbers, got {len(values)}"
            )
        if len(set(values)) != len(values):
            raise DuplicateNumberError(f"Ticket has duplicate numbers: {values}")
        for number in values:
            if not rules.is_in_range(number):
                raise InvalidLotteryNumberError(
                    f"Ticket number {number} outside [{rules.min_number}, {rules.max_number}]"
                )
        return cls(numbers=tuple(sorted(values)))

    def hits_against(self, draw: Draw) -> HitResult:
        hits = len(set(self.numbers) & set(draw.mains))
        additional_match = draw.additional is not None and draw.additional in self.numbers
        return HitResult(hits=hits, additional_match=additional_match)
