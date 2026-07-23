"""SQLite persistence for rebuilt analytics artifacts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Sequence

from atlas.analytics.baseline import DrawBaseline
from atlas.analytics.coappearance import PairStat
from atlas.analytics.number_profiles import NumberProfile


class AnalyticsStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def rebuild(
        self,
        *,
        draws_evaluated: int,
        contest_start: int,
        contest_end: int,
        rolling_windows: Sequence[int],
        profiles: dict[int, NumberProfile],
        pairs: dict[tuple[int, int], PairStat],
        baseline: DrawBaseline,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                DROP TABLE IF EXISTS meta;
                DROP TABLE IF EXISTS number_profiles;
                DROP TABLE IF EXISTS pair_stats;
                DROP TABLE IF EXISTS baseline;
                CREATE TABLE meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE number_profiles (
                    number INTEGER PRIMARY KEY,
                    total_main_count INTEGER NOT NULL,
                    rolling_counts TEXT NOT NULL,
                    recency INTEGER,
                    additional_count INTEGER NOT NULL
                );
                CREATE TABLE pair_stats (
                    left_number INTEGER NOT NULL,
                    right_number INTEGER NOT NULL,
                    count INTEGER NOT NULL,
                    rate REAL NOT NULL,
                    PRIMARY KEY (left_number, right_number)
                );
                CREATE TABLE baseline (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                ("draws_evaluated", str(draws_evaluated)),
            )
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                ("contest_start", str(contest_start)),
            )
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                ("contest_end", str(contest_end)),
            )
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                ("rolling_windows", json.dumps(list(rolling_windows))),
            )
            conn.executemany(
                """
                INSERT INTO number_profiles(
                    number, total_main_count, rolling_counts, recency, additional_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        profile.number,
                        profile.total_main_count,
                        json.dumps(
                            {str(k): v for k, v in sorted(profile.rolling_counts.items())}
                        ),
                        profile.recency,
                        profile.additional_count,
                    )
                    for profile in profiles.values()
                ],
            )
            conn.executemany(
                """
                INSERT INTO pair_stats(left_number, right_number, count, rate)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (pair.left, pair.right, pair.count, pair.rate)
                    for pair in pairs.values()
                ],
            )
            conn.execute(
                "INSERT INTO baseline(id, payload) VALUES (1, ?)",
                (
                    json.dumps(
                        {
                            "draws_evaluated": baseline.draws_evaluated,
                            "sum_min": baseline.sum_min,
                            "sum_max": baseline.sum_max,
                            "sum_mean": baseline.sum_mean,
                            "sum_median": baseline.sum_median,
                            "mean_odd_count": baseline.mean_odd_count,
                            "decade_occupancy_means": baseline.decade_occupancy_means,
                            "consecutive_pair_fraction": baseline.consecutive_pair_fraction,
                        }
                    ),
                ),
            )
            conn.commit()

    def load_profile(self, number: int) -> NumberProfile | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT number, total_main_count, rolling_counts, recency, additional_count
                FROM number_profiles WHERE number = ?
                """,
                (number,),
            ).fetchone()
        if row is None:
            return None
        rolling_raw = json.loads(row[2])
        return NumberProfile(
            number=int(row[0]),
            total_main_count=int(row[1]),
            rolling_counts={int(k): int(v) for k, v in rolling_raw.items()},
            recency=None if row[3] is None else int(row[3]),
            additional_count=int(row[4]),
        )

    def load_top_pairs(self, n: int) -> list[PairStat]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT left_number, right_number, count, rate
                FROM pair_stats
                ORDER BY count DESC, left_number ASC, right_number ASC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
        return [
            PairStat(
                left=int(row[0]),
                right=int(row[1]),
                count=int(row[2]),
                rate=float(row[3]),
            )
            for row in rows
        ]

    def load_baseline(self) -> DrawBaseline:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT payload FROM baseline WHERE id = 1").fetchone()
        if row is None:
            raise FileNotFoundError(f"No baseline stored in {self.db_path}")
        payload = json.loads(row[0])
        return DrawBaseline(
            draws_evaluated=int(payload["draws_evaluated"]),
            sum_min=float(payload["sum_min"]),
            sum_max=float(payload["sum_max"]),
            sum_mean=float(payload["sum_mean"]),
            sum_median=float(payload["sum_median"]),
            mean_odd_count=float(payload["mean_odd_count"]),
            decade_occupancy_means={
                str(k): float(v) for k, v in payload["decade_occupancy_means"].items()
            },
            consecutive_pair_fraction=float(payload["consecutive_pair_fraction"]),
        )

    def draws_evaluated(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM meta WHERE key = 'draws_evaluated'"
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"Analytics meta missing in {self.db_path}")
        return int(row[0])
