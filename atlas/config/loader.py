"""Load ATLAS YAML configuration into typed settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from atlas.config.settings import (
    AciSettings,
    AnalyticsSettings,
    AppConfig,
    BootstrapSettings,
    CoveringOptimizerSettings,
    EloSettings,
    EnsembleOptimizerSettings,
    EvaluationSettings,
    FreezePolicySettings,
    GreedyOptimizerSettings,
    FoldRobustOptimizerSettings,
    LocalSearchOptimizerSettings,
    LotterySettings,
    OptimizerSettings,
    PathSettings,
    PrizeSettings,
    ScoreWeightSettings,
    ScoringSettings,
    TournamentSettings,
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
        covering_raw = optimizer_raw.get("covering") or {}
        local_raw = optimizer_raw.get("local_search") or {}
        fold_robust_raw = optimizer_raw.get("fold_robust") or {}
        ensemble_raw = optimizer_raw.get("ensemble") or {}
        pair_weight = str(covering_raw.get("pair_weight", "train_frequency"))
        if pair_weight not in {"train_frequency", "uniform"}:
            raise ConfigError(
                f"optimizer.covering.pair_weight must be "
                f"'train_frequency' or 'uniform', got {pair_weight!r}"
            )
        cover_orders_raw = covering_raw.get("cover_orders", [2, 3])
        if not isinstance(cover_orders_raw, list) or not cover_orders_raw:
            raise ConfigError(
                "optimizer.covering.cover_orders must be a non-empty list"
            )
        cover_orders = tuple(int(o) for o in cover_orders_raw)
        allowed_orders = {2, 3, 4}
        invalid_orders = [o for o in cover_orders if o not in allowed_orders]
        if invalid_orders:
            raise ConfigError(
                f"optimizer.covering.cover_orders invalid: {invalid_orders}; "
                f"allowed: {sorted(allowed_orders)}"
            )
        if 2 not in cover_orders:
            raise ConfigError(
                "optimizer.covering.cover_orders must include order 2 (pairs)"
            )
        weights_raw = covering_raw.get("order_weights") or {}
        if weights_raw is None:
            weights_raw = {}
        if not isinstance(weights_raw, dict):
            raise ConfigError("optimizer.covering.order_weights must be a mapping")
        parsed_weights = {int(k): float(v) for k, v in weights_raw.items()}
        order_weight_map = {2: 1.0, 3: 1.0, 4: 0.5, **parsed_weights}
        for order, weight in order_weight_map.items():
            if order not in allowed_orders:
                raise ConfigError(
                    f"optimizer.covering.order_weights invalid order: {order}"
                )
            if weight <= 0:
                raise ConfigError(
                    f"optimizer.covering.order_weights[{order}] must be > 0, "
                    f"got {weight}"
                )
        for order in cover_orders:
            if order not in order_weight_map:
                raise ConfigError(
                    f"optimizer.covering.order_weights missing weight for order {order}"
                )
        order_weight_pairs = tuple(sorted(order_weight_map.items()))
        max_passes = int(local_raw.get("max_passes", 20))
        if max_passes < 1:
            raise ConfigError(
                f"optimizer.local_search.max_passes must be >= 1, got {max_passes}"
            )
        fold_robust_max_passes = int(fold_robust_raw.get("max_passes", 20))
        if fold_robust_max_passes < 1:
            raise ConfigError(
                f"optimizer.fold_robust.max_passes must be >= 1, "
                f"got {fold_robust_max_passes}"
            )
        fold_robust_objective = str(fold_robust_raw.get("objective", "absolute"))
        if fold_robust_objective not in {"absolute", "relative"}:
            raise ConfigError(
                f"optimizer.fold_robust.objective must be 'absolute' or 'relative', "
                f"got {fold_robust_objective!r}"
            )
        seeds_raw = ensemble_raw.get("seeds", [42, 7, 99, 123, 256])
        if not isinstance(seeds_raw, list) or not seeds_raw:
            raise ConfigError("optimizer.ensemble.seeds must be a non-empty list")
        seeds = tuple(int(s) for s in seeds_raw)
        sources_raw = ensemble_raw.get("sources", ["greedy", "covering"])
        if not isinstance(sources_raw, list) or not sources_raw:
            raise ConfigError("optimizer.ensemble.sources must be a non-empty list")
        allowed_sources = {"greedy", "covering"}
        sources = tuple(str(s) for s in sources_raw)
        unknown = [s for s in sources if s not in allowed_sources]
        if unknown:
            raise ConfigError(
                f"optimizer.ensemble.sources unknown: {unknown}; "
                f"allowed: {sorted(allowed_sources)}"
            )
        min_hits = int(evaluation_raw["primary_metric_min_hits"])
        optimizer = OptimizerSettings(
            seed=int(optimizer_raw["seed"]),
            candidate_pool_size=int(optimizer_raw["candidate_pool_size"]),
            greedy=GreedyOptimizerSettings(
                enabled=bool(greedy_raw.get("enabled", True)),
            ),
            covering=CoveringOptimizerSettings(
                enabled=bool(covering_raw.get("enabled", True)),
                pair_weight=pair_weight,
                cover_orders=cover_orders,
                order_weights=order_weight_pairs,
            ),
            local_search=LocalSearchOptimizerSettings(
                enabled=bool(local_raw.get("enabled", True)),
                max_passes=max_passes,
                primary_metric_min_hits=min_hits,
            ),
            fold_robust=FoldRobustOptimizerSettings(
                enabled=bool(fold_robust_raw.get("enabled", True)),
                max_passes=fold_robust_max_passes,
                primary_metric_min_hits=min_hits,
                seed_from=(
                    _resolve(root, str(fold_robust_raw["seed_from"]))
                    if fold_robust_raw.get("seed_from") is not None
                    else None
                ),
                objective=fold_robust_objective,
                relative_to=(
                    _resolve(root, str(fold_robust_raw["relative_to"]))
                    if fold_robust_raw.get("relative_to") is not None
                    else None
                ),
            ),
            ensemble=EnsembleOptimizerSettings(
                enabled=bool(ensemble_raw.get("enabled", True)),
                seeds=seeds,
                sources=sources,
                primary_metric_min_hits=min_hits,
            ),
        )

    tournament: TournamentSettings | None = None
    if "tournament" in raw and raw["tournament"] is not None:
        tournament_raw = raw["tournament"]
        tournament = TournamentSettings(
            champion=_resolve(root, str(tournament_raw["champion"])),
            roster_glob=str(tournament_raw["roster_glob"]),
        )

    scoring: ScoringSettings | None = None
    if "scoring" in raw and raw["scoring"] is not None:
        scoring = _load_scoring(raw["scoring"], root)

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
        evaluation=_load_evaluation(evaluation_raw),
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
        tournament=tournament,
        scoring=scoring,
    )


def _load_scoring(scoring_raw: dict[str, Any], root: Path) -> ScoringSettings:
    weights_raw = scoring_raw.get("weights") or {}
    elo_raw = scoring_raw.get("elo") or {}
    aci_raw = scoring_raw.get("aci") or {}
    k_factor = float(elo_raw.get("k_factor", 24))
    if k_factor <= 0:
        raise ConfigError(f"scoring.elo.k_factor must be > 0, got {k_factor}")
    n_resamples = int(aci_raw.get("n_resamples", 1000))
    if n_resamples < 1:
        raise ConfigError(
            f"scoring.aci.n_resamples must be >= 1, got {n_resamples}"
        )
    ci_level = float(aci_raw.get("ci_level", 0.95))
    if not 0.0 < ci_level < 1.0:
        raise ConfigError(
            f"scoring.aci.ci_level must be between 0 and 1, got {ci_level}"
        )
    return ScoringSettings(
        weights=ScoreWeightSettings(
            primary=float(weights_raw.get("primary", 1.0)),
            pairs=float(weights_raw.get("pairs", 0.01)),
            triples=float(weights_raw.get("triples", 0.005)),
            quads=float(weights_raw.get("quads", 0.0)),
        ),
        elo=EloSettings(
            initial_rating=float(elo_raw.get("initial_rating", 1500)),
            k_factor=k_factor,
            ratings_db=_resolve(root, str(elo_raw.get("ratings_db", "data/processed/ratings.sqlite3"))),
        ),
        aci=AciSettings(
            n_resamples=n_resamples,
            ci_level=ci_level,
            seed=int(aci_raw.get("seed", 42)),
        ),
    )


def _load_evaluation(evaluation_raw: dict[str, Any]) -> EvaluationSettings:
    if "freeze_policy" not in evaluation_raw or evaluation_raw["freeze_policy"] is None:
        raise ConfigError(
            "Missing evaluation.freeze_policy configuration "
            "(n_folds, required_fold_passes, bootstrap)"
        )
    freeze_raw = evaluation_raw["freeze_policy"]
    bootstrap_raw = freeze_raw.get("bootstrap") or {}
    n_folds = int(freeze_raw["n_folds"])
    required = int(freeze_raw["required_fold_passes"])
    if n_folds < 2:
        raise ConfigError(f"freeze_policy.n_folds must be >= 2, got {n_folds}")
    if required < 1 or required > n_folds:
        raise ConfigError(
            f"freeze_policy.required_fold_passes must be between 1 and n_folds "
            f"({n_folds}), got {required}"
        )
    ci_level = float(bootstrap_raw.get("ci_level", 0.95))
    if not 0.0 < ci_level < 1.0:
        raise ConfigError(f"bootstrap.ci_level must be between 0 and 1, got {ci_level}")
    n_resamples = int(bootstrap_raw.get("n_resamples", 1000))
    if n_resamples < 1:
        raise ConfigError(
            f"bootstrap.n_resamples must be >= 1, got {n_resamples}"
        )

    min_contest: int | None = None
    if "min_contest" in evaluation_raw and evaluation_raw["min_contest"] is not None:
        min_contest = int(evaluation_raw["min_contest"])
        if min_contest < 1:
            raise ConfigError(
                f"evaluation.min_contest must be >= 1, got {min_contest}"
            )

    return EvaluationSettings(
        validation_ratio=float(evaluation_raw["validation_ratio"]),
        min_absolute_delta=int(evaluation_raw["min_absolute_delta"]),
        primary_metric_min_hits=int(evaluation_raw["primary_metric_min_hits"]),
        freeze_policy=FreezePolicySettings(
            n_folds=n_folds,
            required_fold_passes=required,
            bootstrap=BootstrapSettings(
                enabled=bool(bootstrap_raw.get("enabled", False)),
                n_resamples=n_resamples,
                ci_level=ci_level,
                seed=int(bootstrap_raw.get("seed", 42)),
                min_ci_lower=float(bootstrap_raw.get("min_ci_lower", 0.0)),
            ),
            version=str(freeze_raw.get("version", "walkforward-v1")),
        ),
        min_contest=min_contest,
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


def require_scoring(config: AppConfig) -> ScoringSettings:
    if config.scoring is None:
        raise ConfigError(
            "Missing scoring configuration: add a 'scoring' section to "
            f"{config.source_path}"
        )
    return config.scoring


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()
