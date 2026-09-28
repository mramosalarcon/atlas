"""Analytics contest-floor filtering tests."""

from __future__ import annotations

from pathlib import Path

from atlas.analytics.baseline import compute_draw_baseline
from atlas.analytics.coappearance import compute_coappearance
from atlas.analytics.number_profiles import compute_number_profiles
from atlas.domain.lottery_rules import LotteryRules
from atlas.infrastructure.draw_repository import import_history, load_draws


def _write_csv(path: Path, rows: list[str]) -> None:
    header = "NPRODUCTO,CONCURSO,R1,R2,R3,R4,R5,R6,R7,BOLSA,FECHA"
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_analytics_inputs_honor_min_contest_without_mutating_import(
    tmp_path: Path,
) -> None:
    rules = LotteryRules(1, 56, 6, True, 8)
    csv_path = tmp_path / "history.csv"
    db_path = tmp_path / "raw.sqlite3"
    rows = [
        f"40,{c},{c},{c + 1},{c + 2},{c + 3},{c + 4},{c + 5},{c + 6},0,01/01/2020"
        for c in range(1, 11)
    ]
    _write_csv(csv_path, rows)
    assert import_history(csv_path, db_path, rules) == 10

    full = load_draws(db_path, rules)
    assert [d.contest for d in full] == list(range(1, 11))

    filtered = load_draws(db_path, rules, min_contest=6)
    assert [d.contest for d in filtered] == list(range(6, 11))

    profiles = compute_number_profiles(filtered, rules, rolling_windows=[2])
    pairs = compute_coappearance(filtered, rules)
    baseline = compute_draw_baseline(filtered, rules)
    assert len(profiles) == 56
    assert pairs
    assert baseline.draws_evaluated == 5
    assert [d.contest for d in load_draws(db_path, rules)] == list(range(1, 11))
