"""Elo ratings from freeze-policy duel outcomes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EloUpdate:
    baseline_id: str
    challenger_id: str
    decision: str
    baseline_before: float
    challenger_before: float
    baseline_after: float
    challenger_after: float


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_elo(
    rating_baseline: float,
    rating_challenger: float,
    *,
    decision: str,
    k_factor: float,
) -> tuple[float, float]:
    if decision not in {"accepted", "rejected"}:
        raise ValueError(f"Unsupported decision for Elo update: {decision!r}")
    # Challenger score: 1.0 if accepted else 0.0
    score_challenger = 1.0 if decision == "accepted" else 0.0
    score_baseline = 1.0 - score_challenger
    exp_challenger = expected_score(rating_challenger, rating_baseline)
    exp_baseline = expected_score(rating_baseline, rating_challenger)
    new_challenger = rating_challenger + k_factor * (score_challenger - exp_challenger)
    new_baseline = rating_baseline + k_factor * (score_baseline - exp_baseline)
    return new_baseline, new_challenger


class RatingsStore:
    def __init__(self, path: Path, *, initial_rating: float) -> None:
        self.path = path
        self.initial_rating = initial_rating
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ratings (
                    system_id TEXT PRIMARY KEY,
                    rating REAL NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def get_rating(self, system_id: str) -> float:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT rating FROM ratings WHERE system_id = ?",
                (system_id,),
            ).fetchone()
        if row is None:
            return self.initial_rating
        return float(row[0])

    def set_rating(self, system_id: str, rating: float) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ratings (system_id, rating)
                VALUES (?, ?)
                ON CONFLICT(system_id) DO UPDATE SET
                    rating = excluded.rating,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (system_id, rating),
            )
            conn.commit()

    def list_ratings(self) -> list[tuple[str, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT system_id, rating FROM ratings ORDER BY rating DESC, system_id"
            ).fetchall()
        return [(str(system_id), float(rating)) for system_id, rating in rows]

    def apply_duel(
        self,
        *,
        baseline_id: str,
        challenger_id: str,
        decision: str,
        k_factor: float,
    ) -> EloUpdate:
        baseline_before = self.get_rating(baseline_id)
        challenger_before = self.get_rating(challenger_id)
        baseline_after, challenger_after = update_elo(
            baseline_before,
            challenger_before,
            decision=decision,
            k_factor=k_factor,
        )
        self.set_rating(baseline_id, baseline_after)
        self.set_rating(challenger_id, challenger_after)
        return EloUpdate(
            baseline_id=baseline_id,
            challenger_id=challenger_id,
            decision=decision,
            baseline_before=baseline_before,
            challenger_before=challenger_before,
            baseline_after=baseline_after,
            challenger_after=challenger_after,
        )


def format_ratings_report(ratings: list[tuple[str, float]]) -> str:
    lines = [
        "ATLAS Ratings — historical freeze-policy duel Elo only; "
        "does not predict the next draw and does not replace freeze-policy promotion.",
        f"Systems rated: {len(ratings)}",
    ]
    if not ratings:
        lines.append("(no ratings stored yet)")
    for system_id, rating in ratings:
        lines.append(f"  {system_id}: {rating:.2f}")
    return "\n".join(lines) + "\n"
