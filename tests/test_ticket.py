"""Unit tests for ticket hit counting and validation."""

from __future__ import annotations

import pytest

from atlas.domain.draw import Draw
from atlas.domain.exceptions import InvalidTicketError
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket


@pytest.fixture
def rules() -> LotteryRules:
    return LotteryRules(
        min_number=1,
        max_number=56,
        main_count=6,
        has_additional=True,
        system_size=8,
    )


def test_three_hits(rules: LotteryRules) -> None:
    draw = Draw.create(1, [1, 2, 3, 10, 20, 30], rules, additional=40)
    ticket = Ticket.create([1, 2, 3, 4, 5, 6], rules)
    result = ticket.hits_against(draw)
    assert result.hits == 3
    assert result.additional_match is False


def test_four_hits(rules: LotteryRules) -> None:
    draw = Draw.create(1, [1, 2, 3, 4, 20, 30], rules, additional=40)
    ticket = Ticket.create([1, 2, 3, 4, 5, 6], rules)
    assert ticket.hits_against(draw).hits == 4


def test_perfect_match(rules: LotteryRules) -> None:
    mains = [7, 11, 15, 20, 24, 40]
    draw = Draw.create(1, mains, rules, additional=54)
    ticket = Ticket.create(mains, rules)
    result = ticket.hits_against(draw)
    assert result.hits == 6
    assert result.additional_match is False


def test_additional_match_flag(rules: LotteryRules) -> None:
    draw = Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=10)
    ticket = Ticket.create([1, 2, 3, 10, 20, 30], rules)
    result = ticket.hits_against(draw)
    assert result.hits == 3
    assert result.additional_match is True


def test_invalid_ticket_wrong_count(rules: LotteryRules) -> None:
    with pytest.raises(InvalidTicketError):
        Ticket.create([1, 2, 3], rules)


def test_invalid_ticket_duplicates(rules: LotteryRules) -> None:
    with pytest.raises(Exception):
        Ticket.create([1, 2, 3, 4, 5, 5], rules)


def test_invalid_ticket_out_of_range(rules: LotteryRules) -> None:
    with pytest.raises(Exception):
        Ticket.create([1, 2, 3, 4, 5, 99], rules)
