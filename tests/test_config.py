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


def _freeze_policy(**overrides):
    policy = {
        "n_folds": 5,
        "required_fold_passes": 4,
        "bootstrap": {
            "enabled": False,
            "n_resamples": 1000,
            "ci_level": 0.95,
            "seed": 42,
            "min_ci_lower": 0,
        },
    }
    policy.update(overrides)
    return policy


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
            "freeze_policy": _freeze_policy(),
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
    assert config.evaluation.min_contest == 2088
    assert config.evaluation.freeze_policy.n_folds == 5
    assert config.evaluation.freeze_policy.required_fold_passes == 4
    assert config.evaluation.freeze_policy.bootstrap.enabled is True
    assert config.evaluation.freeze_policy.bootstrap.n_resamples == 1000
    assert config.evaluation.freeze_policy.bootstrap.ci_level == 0.95
    assert config.evaluation.freeze_policy.bootstrap.seed == 42
    assert config.evaluation.freeze_policy.bootstrap.min_ci_lower == 0
    assert config.evaluation.freeze_policy.version == "walkforward-v1+bootstrap"
    assert config.analytics is not None
    assert config.analytics.rolling_windows == (10, 20, 50, 100)
    assert config.optimizer is not None
    assert config.optimizer.seed == 42
    assert config.optimizer.covering.enabled is True
    assert config.optimizer.covering.pair_weight == "train_frequency"
    assert config.optimizer.covering.cover_orders == (2, 3)
    assert config.optimizer.covering.order_weight_map()[2] == 1.0
    assert config.optimizer.covering.order_weight_map()[3] == 1.0
    assert config.optimizer.covering.order_weight_map()[4] == 0.5
    assert config.optimizer.local_search.enabled is True
    assert config.optimizer.local_search.max_passes == 20
    assert config.optimizer.local_search.primary_metric_min_hits == 3
    assert config.optimizer.fold_robust.enabled is True
    assert config.optimizer.fold_robust.max_passes == 20
    assert config.optimizer.fold_robust.primary_metric_min_hits == 3
    assert config.optimizer.fold_robust.seed_from is not None
    assert config.optimizer.fold_robust.seed_from.name == "local_search_candidate.json"
    assert config.optimizer.fold_robust.objective == "absolute"
    assert config.optimizer.ensemble.enabled is True
    assert config.optimizer.ensemble.seeds == (42, 7, 99, 123, 256)
    assert config.optimizer.ensemble.sources == ("greedy", "covering")
    assert config.optimizer.ensemble.primary_metric_min_hits == 3
    assert config.tournament is not None
    assert config.tournament.champion.name == "local_search_candidate.json"
    assert config.tournament.roster_glob == "data/exports/*_candidate.json"
    assert config.scoring is not None
    assert config.scoring.weights.primary == 1.0
    assert config.scoring.weights.pairs == 0.01
    assert config.scoring.elo.k_factor == 24
    assert config.scoring.aci.n_resamples == 1000
    assert config.scoring.aci.ci_level == 0.95
    assert config.scoring.aci.seed == 42



def test_min_contest_omitted_means_no_floor(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_minimal_payload()), encoding="utf-8")
    config = load_config(config_path)
    assert config.evaluation.min_contest is None


def test_min_contest_null_means_no_floor(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload()
    payload["evaluation"]["min_contest"] = None
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.evaluation.min_contest is None


def test_invalid_min_contest_rejects_non_positive(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload()
    payload["evaluation"]["min_contest"] = 0
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="min_contest"):
        load_config(config_path)


def test_tournament_section_absent_is_allowed(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_minimal_payload()), encoding="utf-8")
    config = load_config(config_path)
    assert config.tournament is None


def test_invalid_covering_pair_weight_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "bogus"},
            "local_search": {"enabled": True, "max_passes": 5},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="pair_weight"):
        load_config(config_path)


def test_covering_multi_order_defaults_when_omitted(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "local_search": {"enabled": True, "max_passes": 5},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is not None
    assert config.optimizer.covering.cover_orders == (2, 3)
    assert config.optimizer.covering.order_weight_map()[4] == 0.5


def test_invalid_cover_orders_without_pairs_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "covering": {
                "enabled": True,
                "pair_weight": "train_frequency",
                "cover_orders": [3, 4],
            },
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="order 2"):
        load_config(config_path)


def test_invalid_cover_order_value_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "covering": {
                "enabled": True,
                "pair_weight": "train_frequency",
                "cover_orders": [2, 5],
            },
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="cover_orders"):
        load_config(config_path)


def test_invalid_order_weight_non_positive_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "covering": {
                "enabled": True,
                "pair_weight": "train_frequency",
                "cover_orders": [2, 3],
                "order_weights": {2: 1.0, 3: 0.0},
            },
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="order_weights"):
        load_config(config_path)


def test_invalid_local_search_max_passes_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "local_search": {"enabled": True, "max_passes": 0},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="max_passes"):
        load_config(config_path)


def test_fold_robust_defaults_when_section_omitted(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "local_search": {"enabled": True, "max_passes": 5},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is not None
    assert config.optimizer.fold_robust.enabled is True
    assert config.optimizer.fold_robust.max_passes == 20
    assert config.optimizer.fold_robust.seed_from is None
    assert config.optimizer.fold_robust.objective == "absolute"
    assert config.optimizer.fold_robust.relative_to is None


def test_fold_robust_relative_objective_and_relative_to(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    baseline = tmp_path / "baseline.json"
    baseline.write_text('{"tickets": []}', encoding="utf-8")
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "fold_robust": {
                "enabled": True,
                "max_passes": 5,
                "objective": "relative",
                "relative_to": str(baseline),
            },
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is not None
    assert config.optimizer.fold_robust.objective == "relative"
    assert config.optimizer.fold_robust.relative_to == baseline.resolve()


def test_invalid_fold_robust_objective_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "fold_robust": {"enabled": True, "max_passes": 5, "objective": "soft"},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="objective"):
        load_config(config_path)


def test_fold_robust_null_seed_from_means_covering(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "fold_robust": {"enabled": True, "max_passes": 5, "seed_from": None},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is not None
    assert config.optimizer.fold_robust.seed_from is None


def test_invalid_fold_robust_max_passes_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "fold_robust": {"enabled": True, "max_passes": 0},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="fold_robust.max_passes"):
        load_config(config_path)


def test_ensemble_defaults_when_section_omitted(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "greedy": {"enabled": True},
            "covering": {"enabled": True, "pair_weight": "train_frequency"},
            "local_search": {"enabled": True, "max_passes": 5},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.optimizer is not None
    assert config.optimizer.ensemble.enabled is True
    assert config.optimizer.ensemble.seeds == (42, 7, 99, 123, 256)
    assert config.optimizer.ensemble.sources == ("greedy", "covering")


def test_invalid_ensemble_empty_seeds_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "ensemble": {"enabled": True, "seeds": [], "sources": ["greedy"]},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="seeds"):
        load_config(config_path)


def test_invalid_ensemble_unknown_source_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        optimizer={
            "seed": 1,
            "candidate_pool_size": 10,
            "ensemble": {
                "enabled": True,
                "seeds": [1],
                "sources": ["local_search"],
            },
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="sources"):
        load_config(config_path)


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


def test_invalid_required_fold_passes_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload()
    payload["evaluation"]["freeze_policy"] = _freeze_policy(
        n_folds=3, required_fold_passes=5
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="required_fold_passes"):
        load_config(config_path)


def test_n_folds_must_be_at_least_two(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload()
    payload["evaluation"]["freeze_policy"] = _freeze_policy(
        n_folds=1, required_fold_passes=1
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="n_folds"):
        load_config(config_path)


def test_invalid_bootstrap_n_resamples_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload()
    policy = _freeze_policy()
    policy["bootstrap"]["n_resamples"] = 0
    payload["evaluation"]["freeze_policy"] = policy
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="n_resamples"):
        load_config(config_path)


def test_scoring_section_absent_is_allowed(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_minimal_payload()), encoding="utf-8")
    config = load_config(config_path)
    assert config.scoring is None


def test_invalid_scoring_k_factor_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        scoring={
            "weights": {"primary": 1.0, "pairs": 0.01, "triples": 0.005, "quads": 0.0},
            "elo": {"initial_rating": 1500, "k_factor": 0, "ratings_db": "r.sqlite3"},
            "aci": {"n_resamples": 10, "ci_level": 0.95, "seed": 1},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="k_factor"):
        load_config(config_path)


def test_invalid_scoring_aci_n_resamples_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = _minimal_payload(
        scoring={
            "elo": {"k_factor": 24, "ratings_db": "r.sqlite3"},
            "aci": {"n_resamples": 0, "ci_level": 0.95, "seed": 1},
        }
    )
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ConfigError, match="n_resamples"):
        load_config(config_path)
