"""Load ATLAS YAML configuration into typed settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from atlas.config.settings import (
    AnalyticsSettings,
    AppConfig,
    EvaluationSettings,
    GreedyOptimizerSettings,
    LotterySettings,
    OptimizerSettings,
    PathSettings,
    PrizeSettings,
)


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    root = config_path.resolve().parent.parent
    paths_raw = raw["paths"]
    lottery_raw = raw["lottery"]
    evaluation_raw = raw["evaluation"]
    prizes_raw = raw["prizes"]

    analytics: AnalyticsSettings | None = None
    if "analytics" in raw and raw["analytics"] is not None:
        analytics_raw = raw["analytics"]
        windows = tuple(int(w) for w in analytics_raw["rolling_windows"])
        analytics = AnalyticsSettings(
            rolling_windows=windows,
            analytics_db=_resolve(root, analytics_raw["analytics_db"]),
        )

    optimizer: OptimizerSettings | None = None
    if "optimizer" in raw and raw["optimizer"] is not None:
        optimizer_raw = raw["optimizer"]
        greedy_raw = optimizer_raw.get("greedy") or {}
        optimizer = OptimizerSettings(
            seed=int(optimizer_raw["seed"]),
            candidate_pool_size=int(optimizer_raw["candidate_pool_size"]),
            greedy=GreedyOptimizerSettings(
                enabled=bool(greedy_raw.get("enabled", True)),
            ),
        )

    return AppConfig(
        paths=PathSettings(
            csv=_resolve(root, paths_raw["csv"]),
            raw_db=_resolve(root, paths_raw["raw_db"]),
            experiments_db=_resolve(root, paths_raw["experiments_db"]),
        ),
        lottery=LotterySettings(
            name=str(lottery_raw["name"]),
            min_number=int(lottery_raw["min_number"]),
            max_number=int(lottery_raw["max_number"]),
            main_count=int(lottery_raw["main_count"]),
            has_additional=bool(lottery_raw["has_additional"]),
            system_size=int(lottery_raw["system_size"]),
        ),
        evaluation=EvaluationSettings(
            validation_ratio=float(evaluation_raw["validation_ratio"]),
            min_absolute_delta=int(evaluation_raw["min_absolute_delta"]),
            primary_metric_min_hits=int(evaluation_raw["primary_metric_min_hits"]),
        ),
        prizes=PrizeSettings(
            provisional=bool(prizes_raw["provisional"]),
            ticket_cost=float(prizes_raw["ticket_cost"]),
            hits_3=float(prizes_raw["hits_3"]),
            hits_4=float(prizes_raw["hits_4"]),
            hits_5=float(prizes_raw["hits_5"]),
            hits_5_plus_additional=float(prizes_raw["hits_5_plus_additional"]),
            hits_6=float(prizes_raw["hits_6"]),
        ),
        source_path=config_path,
        analytics=analytics,
        optimizer=optimizer,
    )


def require_analytics(config: AppConfig) -> AnalyticsSettings:
    if config.analytics is None:
        raise ConfigError(
            "Missing analytics configuration: add an 'analytics' section to "
            f"{config.source_path}"
        )
    return config.analytics


def require_optimizer(config: AppConfig) -> OptimizerSettings:
    if config.optimizer is None:
        raise ConfigError(
            "Missing optimizer configuration: add an 'optimizer' section to "
            f"{config.source_path}"
        )
    return config.optimizer


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()
