"""Fixed-size collection of tickets (a playable system)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.domain.exceptions import InvalidSystemError
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket


@dataclass(frozen=True)
class TicketSystem:
    tickets: tuple[Ticket, ...]
    name: str = "system"

    @classmethod
    def create(
        cls,
        tickets: Sequence[Ticket],
        rules: LotteryRules,
        *,
        name: str = "system",
    ) -> TicketSystem:
        values = tuple(tickets)
        if len(values) != rules.system_size:
            raise InvalidSystemError(
                f"System must contain {rules.system_size} tickets, got {len(values)}"
            )
        return cls(tickets=values, name=name)

    def as_number_lists(self) -> list[list[int]]:
        return [list(ticket.numbers) for ticket in self.tickets]
