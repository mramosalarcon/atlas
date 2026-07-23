"""Config loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from atlas.config import (
    ConfigError,
    load_config,
    require_analytics,
    require_optimizer,
)


def _minimal_payload(**overrides):
    payload = {
        "paths": {
            "csv": "data/raw/Melate.csv",
            "raw_db": "data/processed/raw_history.sqlite3",
            "experiments_db": "data/processed/experiments.sqlite3",
        },
        "lottery": {
            "name": "Melate",
            "min_number": 1,
            "max_number": 56,
            "main_count": 6,
            "has_additional": True,
            "system_size": 8,
        },
        "evaluation": {
            "validation_ratio": 0.15,
            "min_absolute_delta": 1,
            "primary_metric_min_hits": 3,
        },
        "prizes": {
            "provisional": True,
            "ticket_cost": 15.0,
            "hits_3": 40.0,
            "hits_4": 1000.0,
            "hits_5": 130000.0,
            "hits_5_plus_additional": 150000.0,
            "hits_6": 30000000.0,
        },
    }
    payload.update(overrides)
    return payload


def test_load_default_melate_config() -> None:
    config = load_config(Path("config/config.yaml"))
    assert config.lottery.min_number == 1
    assert config.lottery.max_number == 56
    assert config.lottery.main_count == 6
    assert config.lottery.system_size == 8
    assert config.evaluation.validation_ratio == 0.15
    assert config.analytics is not None
    assert config.analytics.rolling_windows == (10, 20, 50, 100)
    assert config.analytics.analytics_db.name == "analytics.sqlite3"
    assert config.optimizer is not None
    assert config.optimizer.seed == 42
    assert config.optimizer.candidate_pool_size == 500
    assert config.optimizer.greedy.enabled is True


def test_missing_config_fails_clearly(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match=str(missing)):
        load_config(missing)


def test_missing_analytics_section_fails_when_required(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_minimal_payload()), encoding="utf-8")
    config = load_config(config_path)
    assert config.analytics is None
    with pytest.raises(ConfigError, match="analytics"):
        require_analytics(config)


def test_missing_optimizer_section_fails_when_required(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_minimal_payload()), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is None
    with pytest.raises(ConfigError, match="optimizer"):
        require_optimizer(config)
