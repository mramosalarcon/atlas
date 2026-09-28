"""Draw import validation and SQLite persistence tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.domain.exceptions import ImportValidationError, InvalidDrawError, InvalidLotteryNumberError
from atlas.domain.lottery_rules import LotteryRules
from atlas.infrastructure.draw_repository import (
    import_history,
    load_draws,
    load_draws_for_evaluation,
    parse_melate_csv,
)


@pytest.fixture
def rules() -> LotteryRules:
    return LotteryRules(1, 56, 6, True, 8)


def _write_csv(path: Path, rows: list[str]) -> None:
    header = "NPRODUCTO,CONCURSO,R1,R2,R3,R4,R5,R6,R7,BOLSA,FECHA"
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_successful_import_and_rebuild(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "ok.csv"
    db_path = tmp_path / "raw.sqlite3"
    _write_csv(
        csv_path,
        [
            "40,1,1,2,3,4,5,6,7,100,01/01/2020",
            "40,2,8,9,10,11,12,13,14,200,02/01/2020",
        ],
    )
    assert import_history(csv_path, db_path, rules) == 2
    original = csv_path.read_text(encoding="utf-8")
    assert import_history(csv_path, db_path, rules) == 2
    assert csv_path.read_text(encoding="utf-8") == original
    draws = load_draws(db_path, rules)
    assert [d.contest for d in draws] == [1, 2]
    assert draws[0].mains == (1, 2, 3, 4, 5, 6)
    assert draws[0].additional == 7


def test_out_of_range_fails(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "bad.csv"
    _write_csv(csv_path, ["40,1,1,2,3,4,5,99,7,0,01/01/2020"])
    with pytest.raises(InvalidLotteryNumberError, match="Contest 1"):
        parse_melate_csv(csv_path, rules)


def test_duplicate_mains_fail(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "dup.csv"
    _write_csv(csv_path, ["40,1,1,2,3,4,5,5,7,0,01/01/2020"])
    with pytest.raises(Exception, match="Contest 1"):
        parse_melate_csv(csv_path, rules)


def test_unsorted_mains_fail(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "unsorted.csv"
    _write_csv(csv_path, ["40,1,6,5,4,3,2,1,7,0,01/01/2020"])
    with pytest.raises(InvalidDrawError, match="Contest 1"):
        parse_melate_csv(csv_path, rules)


def test_duplicate_contest_fails(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "dup_contest.csv"
    _write_csv(
        csv_path,
        [
            "40,1,1,2,3,4,5,6,7,0,01/01/2020",
            "40,1,8,9,10,11,12,13,14,0,02/01/2020",
        ],
    )
    with pytest.raises(ImportValidationError, match="Duplicate contest id: 1"):
        parse_melate_csv(csv_path, rules)


def test_gap_in_sequence_fails(tmp_path: Path, rules: LotteryRules) -> None:
    csv_path = tmp_path / "gap.csv"
    _write_csv(
        csv_path,
        [
            "40,1,1,2,3,4,5,6,7,0,01/01/2020",
            "40,3,8,9,10,11,12,13,14,0,02/01/2020",
        ],
    )
    with pytest.raises(ImportValidationError, match="Missing contest id: 2"):
        parse_melate_csv(csv_path, rules)


def test_min_contest_filters_load_without_mutating_db(
    tmp_path: Path, rules: LotteryRules
) -> None:
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
    assert [d.contest for d in load_draws(db_path, rules)] == list(range(1, 11))


def test_load_draws_for_evaluation_rejects_empty_window(
    tmp_path: Path, rules: LotteryRules
) -> None:
    csv_path = tmp_path / "history.csv"
    db_path = tmp_path / "raw.sqlite3"
    _write_csv(
        csv_path,
        [
            "40,1,1,2,3,4,5,6,7,0,01/01/2020",
            "40,2,8,9,10,11,12,13,14,0,02/01/2020",
        ],
    )
    import_history(csv_path, db_path, rules)
    with pytest.raises(ImportValidationError, match="min_contest=99"):
        load_draws_for_evaluation(
            db_path,
            rules,
            min_contest=99,
            validation_ratio=0.15,
            n_folds=2,
        )


def test_load_draws_for_evaluation_rejects_too_few_for_folds(
    tmp_path: Path, rules: LotteryRules
) -> None:
    csv_path = tmp_path / "history.csv"
    db_path = tmp_path / "raw.sqlite3"
    rows = [
        f"40,{c},{c},{c + 1},{c + 2},{c + 3},{c + 4},{c + 5},{c + 6},0,01/01/2020"
        for c in range(1, 6)
    ]
    _write_csv(csv_path, rows)
    import_history(csv_path, db_path, rules)
    with pytest.raises(ImportValidationError, match="n_folds=5"):
        load_draws_for_evaluation(
            db_path,
            rules,
            min_contest=3,
            validation_ratio=0.15,
            n_folds=5,
        )
