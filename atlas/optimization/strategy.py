"""Optimization strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from atlas.config.settings import OptimizerSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket_system import TicketSystem


class OptimizationStrategy(ABC):
    """Produces a TicketSystem from a caller-provided draw set (train only)."""

    @abstractmethod
    def optimize(
        self,
        draws: Sequence[Draw],
        rules: LotteryRules,
        settings: OptimizerSettings,
        *,
        name: str = "optimized",
    ) -> TicketSystem:
        """Return a valid system of rules.system_size tickets."""
