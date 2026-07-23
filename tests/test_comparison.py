"""Strategy comparison and experiment log tests."""

from __future__ import annotations

from pathlib import Path

from atlas.config.settings import (
    AppConfig,
    EvaluationSettings,
    LotterySettings,
    PathSettings,
    PrizeSettings,
)
from atlas.domain.draw import Draw
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.comparison import compare_systems
from atlas.evaluation.split import split_train_validation
from atlas.infrastructure.experiment_store import ExperimentStore


def _rules() -> LotteryRules:
    return LotteryRules(1, 56, 6, True, 8)


def _config(tmp_path: Path, min_absolute_delta: int = 1) -> AppConfig:
    return AppConfig(
        paths=PathSettings(
            csv=tmp_path / "x.csv",
            raw_db=tmp_path / "raw.sqlite3",
            experiments_db=tmp_path / "experiments.sqlite3",
        ),
        lottery=LotterySettings("Melate", 1, 56, 6, True, 8),
        evaluation=EvaluationSettings(0.5, min_absolute_delta, 3),
        prizes=PrizeSettings(True, 20.0, 30.0, 200.0, 5000.0, 50000.0, 1_000_000.0),
        source_path=tmp_path / "config.yaml",
    )


def _system(name: str, tickets: list[list[int]]) -> TicketSystem:
    rules = _rules()
    return TicketSystem.create(
        [Ticket.create(t, rules) for t in tickets],
        rules,
        name=name,
    )


def _draws() -> list[Draw]:
    rules = _rules()
    # Contests 1-2 train, 3-4 validation when ratio=0.5
    return [
        Draw.create(1, [50, 51, 52, 53, 54, 55], rules, additional=56),
        Draw.create(2, [50, 51, 52, 53, 54, 55], rules, additional=56),
        Draw.create(3, [1, 2, 3, 10, 20, 30], rules, additional=40),
        Draw.create(4, [1, 2, 3, 4, 20, 30], rules, additional=40),
    ]


BASELINE_TICKETS = [
    [7, 8, 9, 10, 11, 12],
    [13, 14, 15, 16, 17, 18],
    [19, 20, 21, 22, 23, 24],
    [25, 26, 27, 28, 29, 30],
    [31, 32, 33, 34, 35, 36],
    [37, 38, 39, 40, 41, 42],
    [43, 44, 45, 46, 47, 48],
    [49, 50, 51, 52, 53, 54],
]

CANDIDATE_TICKETS = [
    [1, 2, 3, 4, 5, 6],
    [13, 14, 15, 16, 17, 18],
    [19, 20, 21, 22, 23, 24],
    [25, 26, 27, 28, 29, 30],
    [31, 32, 33, 34, 35, 36],
    [37, 38, 39, 40, 41, 42],
    [43, 44, 45, 46, 47, 48],
    [49, 50, 51, 52, 53, 54],
]


def test_chronological_split() -> None:
    train, validation = split_train_validation(_draws(), 0.5)
    assert [d.contest for d in train] == [1, 2]
    assert [d.contest for d in validation] == [3, 4]


def test_accept_on_improvement(tmp_path: Path) -> None:
    config = _config(tmp_path, min_absolute_delta=1)
    store = ExperimentStore(config.paths.experiments_db)
    result = compare_systems(
        _system("baseline", BASELINE_TICKETS),
        _system("candidate", CANDIDATE_TICKETS),
        _draws(),
        config,
        store,
    )
    assert result.outcome == "improved"
    assert result.decision == "accepted"
    assert result.delta >= 1
    assert store.list_experiments()[0].decision == "accepted"


def test_reject_still_logged(tmp_path: Path) -> None:
    config = _config(tmp_path, min_absolute_delta=1)
    store = ExperimentStore(config.paths.experiments_db)
    result = compare_systems(
        _system("baseline", CANDIDATE_TICKETS),
        _system("candidate", BASELINE_TICKETS),
        _draws(),
        config,
        store,
    )
    assert result.decision == "rejected"
    experiments = store.list_experiments()
    assert len(experiments) == 1
    assert experiments[0].decision == "rejected"
