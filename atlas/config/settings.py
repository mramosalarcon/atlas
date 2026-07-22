"""Typed settings loaded from config/config.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathSettings:
    csv: Path
    raw_db: Path
    experiments_db: Path


@dataclass(frozen=True)
class LotterySettings:
    name: str
    min_number: int
    max_number: int
    main_count: int
    has_additional: bool
    system_size: int


@dataclass(frozen=True)
class EvaluationSettings:
    validation_ratio: float
    min_absolute_delta: int
    primary_metric_min_hits: int


@dataclass(frozen=True)
class PrizeSettings:
    provisional: bool
    ticket_cost: float
    hits_3: float
    hits_4: float
    hits_5: float
    hits_5_plus_additional: float
    hits_6: float

    def amount_for(self, hits: int, additional_match: bool) -> float:
        if hits >= 6:
            return self.hits_6
        if hits == 5 and additional_match:
            return self.hits_5_plus_additional
        if hits == 5:
            return self.hits_5
        if hits == 4:
            return self.hits_4
        if hits == 3:
            return self.hits_3
        return 0.0


@dataclass(frozen=True)
class AppConfig:
    paths: PathSettings
    lottery: LotterySettings
    evaluation: EvaluationSettings
    prizes: PrizeSettings
    source_path: Path
