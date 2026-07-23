"""Analytics package for historical diagnostics."""

from atlas.analytics.baseline import DrawBaseline, compute_draw_baseline, format_baseline_report
from atlas.analytics.coappearance import (
    PairStat,
    compute_coappearance,
    format_pairs_report,
    top_pairs,
)
from atlas.analytics.number_profiles import (
    NumberProfile,
    compute_number_profiles,
    format_number_profile_report,
)
from atlas.analytics.store import AnalyticsStore

__all__ = [
    "AnalyticsStore",
    "DrawBaseline",
    "NumberProfile",
    "PairStat",
    "compute_coappearance",
    "compute_draw_baseline",
    "compute_number_profiles",
    "format_baseline_report",
    "format_number_profile_report",
    "format_pairs_report",
    "top_pairs",
]
