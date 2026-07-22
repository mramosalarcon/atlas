"""CSV parsing, validation, and SQLite persistence for Melate history."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from atlas.domain.draw import Draw
from atlas.domain.exceptions import ImportValidationError
from atlas.domain.lottery_rules import LotteryRules


DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def parse_melate_csv(path: Path, rules: LotteryRules) -> list[Draw]:
    if not path.is_file():
        raise ImportValidationError(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"CONCURSO", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "FECHA"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ImportValidationError(
                f"CSV missing required columns. Found: {reader.fieldnames}"
            )
        rows = list(reader)

    draws = [_row_to_draw(row, rules) for row in rows]
    validate_draw_set(draws)
    return sorted(draws, key=lambda d: d.contest)


def _row_to_draw(row: dict[str, str], rules: LotteryRules) -> Draw:
    contest = int(row["CONCURSO"])
    mains = [int(row[f"R{i}"]) for i in range(1, 7)]
    additional = int(row["R7"])
    jackpot = float(row["BOLSA"]) if row.get("BOLSA") not in (None, "") else None
    draw_date = _parse_date(row["FECHA"], contest)
    return Draw.create(
        contest,
        mains,
        rules,
        additional=additional,
        draw_date=draw_date,
        jackpot=jackpot,
        require_sorted=True,
    )


def _parse_date(value: str, contest: int):
    text = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ImportValidationError(f"Contest {contest}: invalid date '{value}'")


def validate_draw_set(draws: Sequence[Draw]) -> None:
    if not draws:
        raise ImportValidationError("No draws found in CSV")

    contests = [draw.contest for draw in draws]
    seen: set[int] = set()
    for contest in contests:
        if contest in seen:
            raise ImportValidationError(f"Duplicate contest id: {contest}")
        seen.add(contest)

    ordered = sorted(contests)
    for previous, current in zip(ordered, ordered[1:]):
        if current != previous + 1:
            raise ImportValidationError(f"Missing contest id: {previous + 1}")


def save_draws(db_path: Path, draws: Iterable[Draw]) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS draws")
        conn.execute(
            """
            CREATE TABLE draws (
                contest INTEGER PRIMARY KEY,
                n1 INTEGER NOT NULL,
                n2 INTEGER NOT NULL,
                n3 INTEGER NOT NULL,
                n4 INTEGER NOT NULL,
                n5 INTEGER NOT NULL,
                n6 INTEGER NOT NULL,
                additional INTEGER,
                draw_date TEXT,
                jackpot REAL
            )
            """
        )
        rows = [
            (
                draw.contest,
                draw.mains[0],
                draw.mains[1],
                draw.mains[2],
                draw.mains[3],
                draw.mains[4],
                draw.mains[5],
                draw.additional,
                draw.draw_date.isoformat() if draw.draw_date else None,
                draw.jackpot,
            )
            for draw in draws
        ]
        conn.executemany(
            """
            INSERT INTO draws (
                contest, n1, n2, n3, n4, n5, n6, additional, draw_date, jackpot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return len(rows)


def load_draws(db_path: Path, rules: LotteryRules) -> list[Draw]:
    if not db_path.is_file():
        raise ImportValidationError(f"Raw database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM draws ORDER BY contest ASC"
        ).fetchall()

    draws: list[Draw] = []
    for row in rows:
        draw_date = (
            datetime.strptime(row["draw_date"], "%Y-%m-%d").date()
            if row["draw_date"]
            else None
        )
        draws.append(
            Draw.create(
                int(row["contest"]),
                [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"], row["n6"]],
                rules,
                additional=row["additional"],
                draw_date=draw_date,
                jackpot=row["jackpot"],
                require_sorted=True,
            )
        )
    return draws


def import_history(csv_path: Path, db_path: Path, rules: LotteryRules) -> int:
    draws = parse_melate_csv(csv_path, rules)
    return save_draws(db_path, draws)
