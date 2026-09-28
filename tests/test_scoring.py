"""Atlas Score, ACI, and Elo tests."""

from __future__ import annotations

from pathlib import Path

from atlas.config.settings import AciSettings, ScoreWeightSettings
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.scoring.aci import compute_aci, compute_pairwise_aci
from atlas.scoring.elo import RatingsStore, expected_score, update_elo
from atlas.scoring.score import compute_atlas_score, format_score_report


def _weights() -> ScoreWeightSettings:
    return ScoreWeightSettings(primary=1.0, pairs=0.01, triples=0.005, quads=0.0)


def _rules() -> LotteryRules:
    return LotteryRules(1, 12, 4, True, 2)


def _system(rules: LotteryRules, tickets: list[list[int]], name: str) -> TicketSystem:
    return TicketSystem.create(
        [Ticket.create(nums, rules) for nums in tickets],
        rules,
        name=name,
    )


def test_atlas_score_is_deterministic() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [8, 9, 10, 11], rules, additional=12),
    ]
    system = _system(rules, [[1, 2, 3, 4], [5, 6, 7, 8]], "a")
    first = compute_atlas_score(system, draws, weights=_weights(), min_hits=3)
    second = compute_atlas_score(system, draws, weights=_weights(), min_hits=3)
    assert first == second


def test_primary_metric_dominates_equal_coverage() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 3, 5], rules, additional=6),
        Draw.create(3, [9, 10, 11, 12], rules, additional=8),
    ]
    # Same tickets structure / coverage potential; stronger primary via overlapping draws.
    strong = _system(rules, [[1, 2, 3, 4], [1, 2, 3, 5]], "strong")
    weak = _system(rules, [[9, 10, 11, 12], [8, 9, 10, 11]], "weak")
    weights = ScoreWeightSettings(primary=1.0, pairs=0.0, triples=0.0, quads=0.0)
    strong_score = compute_atlas_score(strong, draws, weights=weights, min_hits=3)
    weak_score = compute_atlas_score(weak, draws, weights=weights, min_hits=3)
    assert strong_score.primary > weak_score.primary
    assert strong_score.score > weak_score.score


def test_score_report_non_predictive() -> None:
    rules = _rules()
    draws = [Draw.create(1, [1, 2, 3, 4], rules, additional=5)]
    system = _system(rules, [[1, 2, 3, 4], [5, 6, 7, 8]], "s")
    result = compute_atlas_score(system, draws, weights=_weights(), min_hits=3)
    report = format_score_report(
        result, system_name="s", window="holdout", contest_range=(1, 1)
    ).lower()
    assert "does not predict" in report
    assert "does not auto-promote" in report
    assert "atlas-score-v1" in report


def test_aci_seed_reproducible() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 5, 6], rules, additional=7),
        Draw.create(3, [3, 4, 5, 6], rules, additional=8),
    ]
    system = _system(rules, [[1, 2, 3, 4], [5, 6, 7, 8]], "s")
    aci = AciSettings(n_resamples=50, ci_level=0.95, seed=7)
    first = compute_aci(system, draws, weights=_weights(), min_hits=3, aci=aci)
    second = compute_aci(system, draws, weights=_weights(), min_hits=3, aci=aci)
    assert first == second
    assert first.ci_lower <= first.ci_upper


def test_pairwise_aci_delta() -> None:
    rules = _rules()
    draws = [
        Draw.create(1, [1, 2, 3, 4], rules, additional=5),
        Draw.create(2, [1, 2, 3, 5], rules, additional=6),
    ]
    baseline = _system(rules, [[9, 10, 11, 12], [8, 9, 10, 11]], "base")
    candidate = _system(rules, [[1, 2, 3, 4], [1, 2, 3, 5]], "cand")
    aci = AciSettings(n_resamples=40, ci_level=0.9, seed=3)
    result = compute_pairwise_aci(
        baseline, candidate, draws, weights=_weights(), min_hits=3, aci=aci
    )
    assert result.pairwise is True
    assert result.point_score == (
        compute_atlas_score(candidate, draws, weights=_weights(), min_hits=3).score
        - compute_atlas_score(baseline, draws, weights=_weights(), min_hits=3).score
    )


def test_elo_accept_raises_challenger() -> None:
    before_b, before_c = 1500.0, 1500.0
    after_b, after_c = update_elo(
        before_b, before_c, decision="accepted", k_factor=24
    )
    assert after_c > before_c
    assert after_b < before_b
    after_b2, after_c2 = update_elo(
        before_b, before_c, decision="rejected", k_factor=24
    )
    assert after_c2 < before_c
    assert after_b2 > before_b


def test_elo_persistence(tmp_path: Path) -> None:
    store = RatingsStore(tmp_path / "ratings.sqlite3", initial_rating=1500.0)
    store.apply_duel(
        baseline_id="champ",
        challenger_id="challenger",
        decision="accepted",
        k_factor=24,
    )
    reopen = RatingsStore(tmp_path / "ratings.sqlite3", initial_rating=1500.0)
    assert reopen.get_rating("challenger") > 1500.0
    assert reopen.get_rating("champ") < 1500.0
    listed = dict(reopen.list_ratings())
    assert "challenger" in listed
    assert expected_score(1500, 1500) == 0.5
