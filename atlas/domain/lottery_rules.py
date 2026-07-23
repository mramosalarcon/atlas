"""Lottery rules loaded from configuration (game-agnostic domain)."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.config.settings import LotterySettings


@dataclass(frozen=True)
class LotteryRules:
    min_number: int
    max_number: int
    main_count: int
    has_additional: bool
    system_size: int

    @classmethod
    def from_settings(cls, settings: LotterySettings) -> LotteryRules:
        return cls(
            min_number=settings.min_number,
            max_number=settings.max_number,
            main_count=settings.main_count,
            has_additional=settings.has_additional,
            system_size=settings.system_size,
        )

    def is_in_range(self, number: int) -> bool:
        return self.min_number <= number <= self.max_number
