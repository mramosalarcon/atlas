"""Draw baseline analytics tests."""

from __future__ import annotations

from atlas.analytics.baseline import compute_draw_baseline, format_baseline_report
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules


def _rules() -> LotteryRules:
    return LotteryRules(1, 20, 6, True, 8)


def test_sum_stats_and_consecutive_fraction() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=7),  # consecutive yes, sum=21
        Draw.create(2, [1, 3, 5, 7, 9, 11], rules, additional=8),  # consecutive no, sum=36
    ]
    baseline = compute_draw_baseline(draws, rules)
    assert baseline.sum_min == 21
    assert baseline.sum_max == 36
    assert baseline.sum_mean == 28.5
    assert baseline.sum_median == 28.5
    assert baseline.consecutive_pair_fraction == 0.5
    assert baseline.mean_odd_count == 4.5


def test_baseline_report_is_reference_only() -> None:
    rules = _rules()
    draws = [Draw.create(1, [1, 2, 3, 4, 5, 6], rules, additional=7)]
    report = format_baseline_report(compute_draw_baseline(draws, rules)).lower()
    assert "historical" in report
    assert "does not predict" in report
