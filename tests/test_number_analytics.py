"""Number profile analytics tests."""

from __future__ import annotations

from atlas.analytics.number_profiles import (
    compute_number_profiles,
    format_number_profile_report,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


def _rules() -> LotteryRules:
    return LotteryRules(1, 10, 3, True, 8)


def test_rolling_window_uses_newest_draws() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=4),
        Draw.create(2, [1, 2, 3], rules, additional=4),
        Draw.create(3, [4, 5, 6], rules, additional=7),
        Draw.create(4, [4, 5, 6], rules, additional=7),
        Draw.create(5, [4, 5, 6], rules, additional=7),
    ]
    profiles = compute_number_profiles(draws, rules, rolling_windows=[2])
    assert profiles[1].rolling_counts[2] == 0
    assert profiles[4].rolling_counts[2] == 2
    assert profiles[4].total_main_count == 3


def test_never_appeared_recency_is_null() -> None:
    rules = _rules()
    draws = [Draw.create(1, [1, 2, 3], rules, additional=4)]
    profiles = compute_number_profiles(draws, rules, rolling_windows=[10])
    assert profiles[10].total_main_count == 0
    assert profiles[10].recency is None
    assert profiles[1].recency == 0


def test_profiles_deterministic_and_non_predictive() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3], rules, additional=9),
        Draw.create(2, [2, 3, 4], rules, additional=9),
    ]
    first = compute_number_profiles(draws, rules, [10, 20])
    second = compute_number_profiles(draws, rules, [10, 20])
    assert first == second
    assert len(first) == 10
    report = format_number_profile_report(first[2], draws_evaluated=2).lower()
    assert "does not predict" in report
    assert "historical" in report
