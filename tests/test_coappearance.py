"""Co-appearance matrix tests."""

from __future__ import annotations

import pytest

from atlas.analytics.coappearance import (
    compute_coappearance,
    format_pairs_report,
    top_pairs,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


def _rules() -> LotteryRules:
    return LotteryRules(1, 6, 6, True, 8)


def test_pair_counted_once_per_draw_and_rate() -> None:
    rules = _rules()
    draws = [Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=1)]
    stats = compute_coappearance(draws, rules)
    assert stats[(1, 2)].count == 1
    assert stats[(1, 2)].rate == 1.0
    assert (2, 1) not in stats


def test_top_pairs_tie_break_deterministic() -> None:
    rules = LotteryRules(1, 6, 3, True, 8)
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 4], rules, additional=5),
        Draw.create(3, [3, 4, 5], rules, additional=6),
    ]
    stats = compute_coappearance(draws, rules)
    ranked = top_pairs(stats, 3)
    assert ranked[0].pair == (1, 2)
    assert ranked[0].count == 2
    # Next ties at count=1 ordered by ascending pair
    assert ranked[1].count == 1
    assert ranked[1].pair < ranked[2].pair


def test_zero_draws_rejected() -> None:
    with pytest.raises(ValueError, match="zero draws"):
        compute_coappearance([], _rules())


def test_pairs_report_non_predictive() -> None:
    rules = _rules()
    draws = [Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=1)]
    stats = compute_coappearance(draws, rules)
    report = format_pairs_report(top_pairs(stats, 2), 1).lower()
    assert "does not predict" in report
