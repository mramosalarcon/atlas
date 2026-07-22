"""Experiment log persistence (SQLite)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentRecord:
    id: int
    timestamp: str
    baseline_name: str
    candidate_name: str
    baseline_tickets: list[list[int]]
    candidate_tickets: list[list[int]]
    validation_start: int
    validation_end: int
    baseline_metric: int
    candidate_metric: int
    delta: int
    outcome: str
    decision: str
    min_absolute_delta: int
    config_path: str


class ExperimentStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    baseline_name TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    baseline_tickets TEXT NOT NULL,
                    candidate_tickets TEXT NOT NULL,
                    validation_start INTEGER NOT NULL,
                    validation_end INTEGER NOT NULL,
                    baseline_metric INTEGER NOT NULL,
                    candidate_metric INTEGER NOT NULL,
                    delta INTEGER NOT NULL,
                    outcome TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    min_absolute_delta INTEGER NOT NULL,
                    config_path TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def append(self, payload: dict[str, Any]) -> ExperimentRecord:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO experiments (
                    timestamp, baseline_name, candidate_name,
                    baseline_tickets, candidate_tickets,
                    validation_start, validation_end,
                    baseline_metric, candidate_metric, delta,
                    outcome, decision, min_absolute_delta, config_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    payload["baseline_name"],
                    payload["candidate_name"],
                    json.dumps(payload["baseline_tickets"]),
                    json.dumps(payload["candidate_tickets"]),
                    payload["validation_start"],
                    payload["validation_end"],
                    payload["baseline_metric"],
                    payload["candidate_metric"],
                    payload["delta"],
                    payload["outcome"],
                    payload["decision"],
                    payload["min_absolute_delta"],
                    payload["config_path"],
                ),
            )
            conn.commit()
            experiment_id = int(cursor.lastrowid)

        return ExperimentRecord(
            id=experiment_id,
            timestamp=timestamp,
            baseline_name=payload["baseline_name"],
            candidate_name=payload["candidate_name"],
            baseline_tickets=payload["baseline_tickets"],
            candidate_tickets=payload["candidate_tickets"],
            validation_start=payload["validation_start"],
            validation_end=payload["validation_end"],
            baseline_metric=payload["baseline_metric"],
            candidate_metric=payload["candidate_metric"],
            delta=payload["delta"],
            outcome=payload["outcome"],
            decision=payload["decision"],
            min_absolute_delta=payload["min_absolute_delta"],
            config_path=payload["config_path"],
        )

    def list_experiments(self) -> list[ExperimentRecord]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM experiments ORDER BY id ASC"
            ).fetchall()

        return [
            ExperimentRecord(
                id=int(row["id"]),
                timestamp=row["timestamp"],
                baseline_name=row["baseline_name"],
                candidate_name=row["candidate_name"],
                baseline_tickets=json.loads(row["baseline_tickets"]),
                candidate_tickets=json.loads(row["candidate_tickets"]),
                validation_start=int(row["validation_start"]),
                validation_end=int(row["validation_end"]),
                baseline_metric=int(row["baseline_metric"]),
                candidate_metric=int(row["candidate_metric"]),
                delta=int(row["delta"]),
                outcome=row["outcome"],
                decision=row["decision"],
                min_absolute_delta=int(row["min_absolute_delta"]),
                config_path=row["config_path"],
            )
            for row in rows
        ]
