"""Config loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.config import ConfigError, load_config


def test_load_default_melate_config() -> None:
    config = load_config(Path("config/config.yaml"))
    assert config.lottery.min_number == 1
    assert config.lottery.max_number == 56
    assert config.lottery.main_count == 6
    assert config.lottery.system_size == 8
    assert config.evaluation.validation_ratio == 0.15


def test_missing_config_fails_clearly(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match=str(missing)):
        load_config(missing)
