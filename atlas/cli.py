"""ATLAS command-line entrypoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas.analytics import (
    AnalyticsStore,
    compute_coappearance,
    compute_draw_baseline,
    compute_number_profiles,
    format_baseline_report,
    format_number_profile_report,
    format_pairs_report,
    top_pairs,
)
from atlas.config import ConfigError, load_config, require_analytics, require_optimizer, require_scoring
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.comparison import compare_systems
from atlas.evaluation.evaluator import evaluate_system, format_evaluation_report
from atlas.evaluation.split import split_train_validation
from atlas.infrastructure.draw_repository import (
    ImportValidationError,
    import_history,
    load_draws,
    load_draws_for_evaluation,
)
from atlas.infrastructure.experiment_store import ExperimentStore
from atlas.optimization import (
    CoveringOptimizer,
    EnsembleOptimizer,
    EnsemblePoolError,
    FoldRobustOptimizer,
    GreedyOptimizer,
    LocalSearchOptimizer,
    covered_pair_count,
    format_covering_report,
    format_ensemble_report,
    format_fold_robust_report,
    format_local_search_report,
    format_optimize_report,
)
from atlas.optimization.covering import covered_quad_count, covered_triple_count
from atlas.optimization.ensemble import draft_from_pool, pool_tickets_from_files
from atlas.optimization.fold_robust import (
    FoldRobustBaselineError,
    FoldRobustSeedError,
    load_fold_robust_baseline,
    resolve_relative_baseline_path,
)
from atlas.optimization.local_search import pair_coverage_count, primary_metric_count
from atlas.scoring import (
    RatingsStore,
    compute_aci,
    compute_atlas_score,
    compute_pairwise_aci,
    format_aci_report,
    format_ratings_report,
    format_score_report,
)
from atlas.tournament import (
    format_tournament_report,
    resolve_roster,
    run_ladder,
    write_tournament_summary,
)

DEFAULT_CONFIG = Path("config/config.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas",
        description=(
            "ATLAS evaluates and compares Melate strategies on historical data. "
            "It does not predict future draws."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to config YAML (default: config/config.yaml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("import-history", help="Import Melate CSV into the raw SQLite database")

    evaluate = sub.add_parser("evaluate-system", help="Evaluate an 8-ticket system JSON file")
    evaluate.add_argument("system_file", type=Path, help="JSON file with tickets array")

    compare = sub.add_parser(
        "compare-systems",
        help="Compare baseline vs candidate on the validation window and log the experiment",
    )
    compare.add_argument("baseline_file", type=Path)
    compare.add_argument("candidate_file", type=Path)
    compare.add_argument(
        "--with-score",
        action="store_true",
        help="Attach Atlas Score / ACI diagnostics on the holdout window (does not change decision)",
    )
    compare.add_argument(
        "--update-ratings",
        action="store_true",
        help="Update Elo ratings from the freeze-policy decision",
    )

    sub.add_parser("list-experiments", help="List recorded strategy comparison experiments")

    sub.add_parser(
        "build-analytics",
        help="Rebuild number profiles, pair co-appearance, and draw baseline diagnostics",
    )

    show_number = sub.add_parser("show-number", help="Show a stored number profile")
    show_number.add_argument("number", type=int)

    show_pairs = sub.add_parser("show-pairs", help="Show top co-appearing pairs from analytics DB")
    show_pairs.add_argument("--top", type=int, default=10)

    sub.add_parser("show-baseline", help="Show stored draw-shape baseline diagnostics")

    optimize = sub.add_parser(
        "optimize-greedy",
        help=(
            "Build an 8-ticket candidate on the train window via pair-coverage greedy "
            "(does not auto-accept; optional --compare-baseline uses freeze policy)"
        ),
    )
    optimize.add_argument(
        "--output",
        type=Path,
        default=Path("data/exports/greedy_candidate.json"),
        help="Export path for the candidate system JSON",
    )
    optimize.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Optional baseline system JSON to compare against on validation",
    )

    covering = sub.add_parser(
        "optimize-covering",
        help=(
            "Build an 8-ticket candidate on the train window via covering-design "
            "(does not auto-accept; optional --compare-baseline uses freeze policy)"
        ),
    )
    covering.add_argument(
        "--output",
        type=Path,
        default=Path("data/exports/covering_candidate.json"),
        help="Export path for the candidate system JSON",
    )
    covering.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Optional baseline system JSON to compare against on validation",
    )

    local = sub.add_parser(
        "optimize-local",
        help=(
            "Polish a covering-seeded system via train-only local search "
            "(does not auto-accept; optional --compare-baseline uses freeze policy)"
        ),
    )
    local.add_argument(
        "--output",
        type=Path,
        default=Path("data/exports/local_search_candidate.json"),
        help="Export path for the candidate system JSON",
    )
    local.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Optional baseline system JSON to compare against on validation",
    )

    fold_robust = sub.add_parser(
        "optimize-fold-robust",
        help=(
            "Polish a covering- or file-seeded system via fold-robust train-only "
            "local search (does not auto-accept; optional --compare-baseline uses "
            "freeze policy)"
        ),
    )
    fold_robust.add_argument(
        "--output",
        type=Path,
        default=Path("data/exports/fold_robust_candidate.json"),
        help="Export path for the candidate system JSON",
    )
    fold_robust.add_argument(
        "--seed-from",
        type=Path,
        default=None,
        help=(
            "Optional ticket-system JSON to seed hill climb "
            "(overrides optimizer.fold_robust.seed_from; omit both for covering)"
        ),
    )
    fold_robust.add_argument(
        "--objective",
        type=str,
        choices=("absolute", "relative"),
        default=None,
        help=(
            "Fold-robust objective mode (default: config "
            "optimizer.fold_robust.objective)"
        ),
    )
    fold_robust.add_argument(
        "--relative-to",
        type=Path,
        default=None,
        help=(
            "Baseline ticket-system JSON for relative objective "
            "(overrides optimizer.fold_robust.relative_to)"
        ),
    )
    fold_robust.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Optional baseline system JSON to compare against on validation",
    )

    ensemble = sub.add_parser(
        "optimize-ensemble",
        help=(
            "Draft an 8-ticket candidate by pooling multi-seed greedy/covering "
            "tickets and/or --sources JSON files (does not auto-accept; "
            "optional --compare-baseline uses freeze policy)"
        ),
    )
    ensemble.add_argument(
        "--output",
        type=Path,
        default=Path("data/exports/ensemble_candidate.json"),
        help="Export path for the candidate system JSON",
    )
    ensemble.add_argument(
        "--sources",
        type=Path,
        nargs="*",
        default=[],
        help="Optional system JSON files whose tickets are unioned into the pool",
    )
    ensemble.add_argument(
        "--files-only",
        action="store_true",
        help="Skip multi-seed generate; draft only from --sources files",
    )
    ensemble.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Optional baseline system JSON to compare against on validation",
    )

    tournament = sub.add_parser(
        "run-tournament",
        help=(
            "Run a ladder tournament: challengers face the current champion under "
            "freeze policy (does not predict future draws)"
        ),
    )
    tournament.add_argument(
        "--champion",
        type=Path,
        default=None,
        help="Champion system JSON (defaults to config tournament.champion)",
    )
    tournament.add_argument(
        "--challengers",
        type=Path,
        nargs="*",
        default=[],
        help="Explicit challenger system JSON paths",
    )
    tournament.add_argument(
        "--roster-glob",
        type=str,
        default=None,
        help="Glob for challenger JSONs (defaults to config tournament.roster_glob)",
    )
    tournament.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write tournament summary JSON",
    )
    tournament.add_argument(
        "--update-ratings",
        action="store_true",
        help="Update Elo ratings after each duel from freeze-policy decisions",
    )

    score_cmd = sub.add_parser(
        "score-system",
        help=(
            "Compute Atlas Score for a system JSON (historical diagnostic only; "
            "does not promote champions)"
        ),
    )
    score_cmd.add_argument("system_file", type=Path)
    score_cmd.add_argument(
        "--window",
        choices=("holdout", "train", "all"),
        default="holdout",
        help="Draw window for scoring (default: holdout)",
    )

    aci_cmd = sub.add_parser(
        "score-aci",
        help=(
            "Compute Atlas Confidence Interval around Atlas Score "
            "(historical diagnostic only)"
        ),
    )
    aci_cmd.add_argument("system_file", type=Path)
    aci_cmd.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional baseline for pairwise score-delta ACI",
    )
    aci_cmd.add_argument(
        "--window",
        choices=("holdout", "train", "all"),
        default="holdout",
        help="Draw window for ACI (default: holdout)",
    )

    sub.add_parser("show-ratings", help="List persisted Atlas Elo ratings")

    update_ratings = sub.add_parser(
        "update-ratings",
        help="Apply an Elo update from a freeze-policy decision for two system identities",
    )
    update_ratings.add_argument("baseline_id", type=str, help="Baseline/champion identity")
    update_ratings.add_argument("challenger_id", type=str, help="Challenger identity")
    update_ratings.add_argument(
        "decision",
        choices=("accepted", "rejected"),
        help="Freeze-policy decision from the duel",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rules = LotteryRules.from_settings(config.lottery)

    if args.command == "import-history":
        count = import_history(config.paths.csv, config.paths.raw_db, rules)
        print(f"Imported {count} draws into {config.paths.raw_db}")
        print(f"Source CSV left unchanged: {config.paths.csv}")
        return 0

    if args.command == "evaluate-system":
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        system = _load_system(args.system_file, rules, name=args.system_file.stem)
        result = evaluate_system(system, draws, rules, config.prizes)
        print(format_evaluation_report(result, system.name))
        if config.evaluation.min_contest is not None:
            print(
                f"Contest floor applied: evaluation.min_contest="
                f"{config.evaluation.min_contest} "
                f"(contests {draws[0].contest}–{draws[-1].contest})"
            )
        return 0

    if args.command == "compare-systems":
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        baseline = _load_system(args.baseline_file, rules, name=args.baseline_file.stem)
        candidate = _load_system(args.candidate_file, rules, name=args.candidate_file.stem)
        store = ExperimentStore(config.paths.experiments_db)
        comparison = compare_systems(baseline, candidate, draws, config, store)
        _print_comparison(comparison)
        if args.with_score:
            try:
                scoring = require_scoring(config)
            except ConfigError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            _, holdout = split_train_validation(
                draws, config.evaluation.validation_ratio
            )
            min_hits = config.evaluation.primary_metric_min_hits
            base_score = compute_atlas_score(
                baseline, holdout, weights=scoring.weights, min_hits=min_hits
            )
            cand_score = compute_atlas_score(
                candidate, holdout, weights=scoring.weights, min_hits=min_hits
            )
            pairwise = compute_pairwise_aci(
                baseline,
                candidate,
                holdout,
                weights=scoring.weights,
                min_hits=min_hits,
                aci=scoring.aci,
            )
            print(
                "Atlas Score / ACI diagnostics (holdout; do not change decision): "
                f"baseline={base_score.score:.4f} candidate={cand_score.score:.4f} "
                f"delta_ACI=[{pairwise.ci_lower:.4f}, {pairwise.ci_upper:.4f}]"
            )
        if args.update_ratings:
            try:
                scoring = require_scoring(config)
            except ConfigError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            ratings = RatingsStore(
                scoring.elo.ratings_db,
                initial_rating=scoring.elo.initial_rating,
            )
            update = ratings.apply_duel(
                baseline_id=baseline.name,
                challenger_id=candidate.name,
                decision=comparison.decision,
                k_factor=scoring.elo.k_factor,
            )
            print(
                f"Elo updated ({update.decision}): "
                f"{update.baseline_id} {update.baseline_before:.2f}->{update.baseline_after:.2f}, "
                f"{update.challenger_id} {update.challenger_before:.2f}->{update.challenger_after:.2f}"
            )
        return 0

    if args.command == "list-experiments":
        store = ExperimentStore(config.paths.experiments_db)
        experiments = store.list_experiments()
        if not experiments:
            print("No experiments recorded.")
            return 0
        for experiment in experiments:
            floor = (
                f" min_contest={experiment.min_contest}"
                if experiment.min_contest is not None
                else ""
            )
            print(
                f"#{experiment.id} {experiment.timestamp} "
                f"{experiment.baseline_name}->{experiment.candidate_name} "
                f"delta={experiment.delta} decision={experiment.decision}{floor}"
            )
        return 0

    if args.command == "build-analytics":
        try:
            analytics = require_analytics(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            draws = load_draws(
                config.paths.raw_db,
                rules,
                min_contest=config.evaluation.min_contest,
            )
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not draws:
            floor_note = (
                f" (evaluation.min_contest={config.evaluation.min_contest})"
                if config.evaluation.min_contest is not None
                else ""
            )
            print(
                f"error: no draws available for analytics{floor_note}",
                file=sys.stderr,
            )
            return 1
        profiles = compute_number_profiles(draws, rules, analytics.rolling_windows)
        pairs = compute_coappearance(draws, rules)
        baseline = compute_draw_baseline(draws, rules)
        store = AnalyticsStore(analytics.analytics_db)
        store.rebuild(
            draws_evaluated=len(draws),
            contest_start=draws[0].contest,
            contest_end=draws[-1].contest,
            rolling_windows=analytics.rolling_windows,
            profiles=profiles,
            pairs=pairs,
            baseline=baseline,
        )
        print(
            "ATLAS analytics rebuilt — historical diagnostics only; "
            "does not predict the next draw."
        )
        if config.evaluation.min_contest is not None:
            print(
                f"Contest floor applied: evaluation.min_contest="
                f"{config.evaluation.min_contest}"
            )
        print(f"Draws: {len(draws)} (contests {draws[0].contest}–{draws[-1].contest})")
        print(f"Analytics DB: {analytics.analytics_db}")
        print(f"Raw DB left unchanged: {config.paths.raw_db}")
        return 0

    if args.command == "show-number":
        try:
            analytics = require_analytics(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        store = AnalyticsStore(analytics.analytics_db)
        profile = store.load_profile(args.number)
        if profile is None:
            print(f"error: no profile for number {args.number}", file=sys.stderr)
            return 1
        print(format_number_profile_report(profile, store.draws_evaluated()))
        return 0

    if args.command == "show-pairs":
        try:
            analytics = require_analytics(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        store = AnalyticsStore(analytics.analytics_db)
        pairs = store.load_top_pairs(args.top)
        print(format_pairs_report(pairs, store.draws_evaluated()))
        return 0

    if args.command == "show-baseline":
        try:
            analytics = require_analytics(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        store = AnalyticsStore(analytics.analytics_db)
        print(format_baseline_report(store.load_baseline()))
        return 0

    if args.command == "optimize-greedy":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.greedy.enabled:
            print("error: optimizer.greedy.enabled is false", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        train, _validation = split_train_validation(
            draws, config.evaluation.validation_ratio
        )
        system = GreedyOptimizer().optimize(
            train,
            rules,
            optimizer_settings,
            name="greedy",
        )
        _write_system(args.output, system)
        print(
            format_optimize_report(
                system,
                seed=optimizer_settings.seed,
                train_contests=(train[0].contest, train[-1].contest),
                pairs_covered=covered_pair_count(system),
            )
        )
        print(f"Exported candidate: {args.output}")
        print(
            "Accept/reject requires freeze-policy compare "
            "(pass --compare-baseline or run compare-systems)."
        )
        if args.compare_baseline is not None:
            baseline = _load_system(
                args.compare_baseline, rules, name=args.compare_baseline.stem
            )
            store = ExperimentStore(config.paths.experiments_db)
            comparison = compare_systems(baseline, system, draws, config, store)
            _print_comparison(comparison)
        return 0

    if args.command == "optimize-covering":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.covering.enabled:
            print("error: optimizer.covering.enabled is false", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        train, _validation = split_train_validation(
            draws, config.evaluation.validation_ratio
        )
        system = CoveringOptimizer().optimize(
            train,
            rules,
            optimizer_settings,
            name="covering",
        )
        _write_system(args.output, system)
        print(
            format_covering_report(
                system,
                seed=optimizer_settings.seed,
                pair_weight=optimizer_settings.covering.pair_weight,
                train_contests=(train[0].contest, train[-1].contest),
                pairs_covered=covered_pair_count(system),
                triples_covered=covered_triple_count(system),
                quads_covered=covered_quad_count(system),
                cover_orders=optimizer_settings.covering.cover_orders,
            )
        )
        print(f"Exported candidate: {args.output}")
        print(
            "Accept/reject requires freeze-policy compare "
            "(pass --compare-baseline or run compare-systems)."
        )
        if args.compare_baseline is not None:
            baseline = _load_system(
                args.compare_baseline, rules, name=args.compare_baseline.stem
            )
            store = ExperimentStore(config.paths.experiments_db)
            comparison = compare_systems(baseline, system, draws, config, store)
            _print_comparison(comparison)
        return 0

    if args.command == "optimize-local":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.local_search.enabled:
            print("error: optimizer.local_search.enabled is false", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        train, _validation = split_train_validation(
            draws, config.evaluation.validation_ratio
        )
        optimizer = LocalSearchOptimizer()
        system = optimizer.optimize(
            train,
            rules,
            optimizer_settings,
            name="local-search",
        )
        _write_system(args.output, system)
        print(
            format_local_search_report(
                system,
                seed=optimizer_settings.seed,
                max_passes=optimizer_settings.local_search.max_passes,
                train_contests=(train[0].contest, train[-1].contest),
                train_metric=optimizer.last_train_metric,
                pairs_covered=optimizer.last_pairs_covered,
                triples_covered=optimizer.last_triples_covered,
                quads_covered=optimizer.last_quads_covered,
                accepts=optimizer.last_accepts,
            )
        )
        print(f"Exported candidate: {args.output}")
        print(
            "Accept/reject requires freeze-policy compare "
            "(pass --compare-baseline or run compare-systems)."
        )
        if args.compare_baseline is not None:
            baseline = _load_system(
                args.compare_baseline, rules, name=args.compare_baseline.stem
            )
            store = ExperimentStore(config.paths.experiments_db)
            comparison = compare_systems(baseline, system, draws, config, store)
            _print_comparison(comparison)
        return 0

    if args.command == "optimize-fold-robust":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.fold_robust.enabled:
            print("error: optimizer.fold_robust.enabled is false", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        train, _validation = split_train_validation(
            draws, config.evaluation.validation_ratio
        )
        n_folds = config.evaluation.freeze_policy.n_folds
        seed_from = args.seed_from
        if seed_from is None:
            seed_from = optimizer_settings.fold_robust.seed_from
        objective = args.objective or optimizer_settings.fold_robust.objective
        relative_baseline = None
        relative_baseline_path: str | None = None
        if objective == "relative":
            try:
                baseline_path = resolve_relative_baseline_path(
                    cli_relative_to=args.relative_to,
                    relative_to=optimizer_settings.fold_robust.relative_to,
                    seed_from=seed_from,
                    tournament_champion=(
                        config.tournament.champion
                        if config.tournament is not None
                        else None
                    ),
                )
                relative_baseline = load_fold_robust_baseline(
                    baseline_path, rules, name=baseline_path.stem
                )
                relative_baseline_path = str(baseline_path)
            except FoldRobustBaselineError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
        optimizer = FoldRobustOptimizer(
            n_folds=n_folds,
            seed_from=seed_from,
            objective=objective,
            relative_baseline=relative_baseline,
            min_absolute_delta=config.evaluation.min_absolute_delta,
            relative_baseline_path=relative_baseline_path,
        )
        try:
            system = optimizer.optimize(
                train,
                rules,
                optimizer_settings,
                name="fold-robust",
            )
        except (FoldRobustSeedError, FoldRobustBaselineError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        _write_system(args.output, system)
        print(
            format_fold_robust_report(
                system,
                seed=optimizer_settings.seed,
                max_passes=optimizer_settings.fold_robust.max_passes,
                n_folds=n_folds,
                train_contests=(train[0].contest, train[-1].contest),
                min_fold=optimizer.last_min_fold,
                sum_fold=optimizer.last_sum_fold,
                train_metric=optimizer.last_train_metric,
                fold_primaries=optimizer.last_fold_primaries,
                pairs_covered=optimizer.last_pairs_covered,
                triples_covered=optimizer.last_triples_covered,
                quads_covered=optimizer.last_quads_covered,
                accepts=optimizer.last_accepts,
                seed_source=optimizer.last_seed_source,
                objective=optimizer.last_objective,
                relative_baseline=optimizer.relative_baseline_path,
                fold_deltas=optimizer.last_fold_deltas or None,
                train_fold_passes=optimizer.last_train_fold_passes,
                sum_deltas=optimizer.last_sum_deltas,
                min_absolute_delta=config.evaluation.min_absolute_delta,
            )
        )
        print(f"Exported candidate: {args.output}")
        print(
            "Accept/reject requires freeze-policy compare "
            "(pass --compare-baseline or run compare-systems)."
        )
        if args.compare_baseline is not None:
            baseline = _load_system(
                args.compare_baseline, rules, name=args.compare_baseline.stem
            )
            store = ExperimentStore(config.paths.experiments_db)
            comparison = compare_systems(baseline, system, draws, config, store)
            _print_comparison(comparison)
        return 0

    if args.command == "optimize-ensemble":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.ensemble.enabled:
            print("error: optimizer.ensemble.enabled is false", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        train, _validation = split_train_validation(
            draws, config.evaluation.validation_ratio
        )
        file_pool = (
            pool_tickets_from_files(args.sources, rules) if args.sources else {}
        )
        if args.files_only:
            if not file_pool:
                print(
                    "error: --files-only requires at least one --sources file",
                    file=sys.stderr,
                )
                return 1
            try:
                tickets = draft_from_pool(
                    file_pool,
                    train,
                    rules,
                    min_hits=optimizer_settings.ensemble.primary_metric_min_hits,
                )
            except EnsemblePoolError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            system = TicketSystem.create(tickets, rules, name="ensemble")
            pool_size = len(file_pool)
            seeds: tuple[int, ...] = ()
            sources = tuple(str(p) for p in args.sources)
            train_metric = primary_metric_count(
                system,
                train,
                min_hits=optimizer_settings.ensemble.primary_metric_min_hits,
            )
            pairs = pair_coverage_count(system)
        else:
            optimizer = EnsembleOptimizer()
            try:
                system = optimizer.optimize(
                    train,
                    rules,
                    optimizer_settings,
                    name="ensemble",
                    extra_pool=file_pool or None,
                )
            except EnsemblePoolError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            pool_size = optimizer.last_pool_size
            seeds = optimizer.last_seeds
            sources = optimizer.last_sources
            if args.sources:
                sources = sources + tuple(str(p) for p in args.sources)
            train_metric = optimizer.last_train_metric
            pairs = optimizer.last_pairs_covered
        _write_system(args.output, system)
        print(
            format_ensemble_report(
                system,
                seeds=seeds,
                sources=sources,
                pool_size=pool_size,
                train_contests=(train[0].contest, train[-1].contest),
                train_metric=train_metric,
                pairs_covered=pairs,
            )
        )
        print(f"Exported candidate: {args.output}")
        print(
            "Accept/reject requires freeze-policy compare "
            "(pass --compare-baseline or run compare-systems)."
        )
        if args.compare_baseline is not None:
            baseline = _load_system(
                args.compare_baseline, rules, name=args.compare_baseline.stem
            )
            store = ExperimentStore(config.paths.experiments_db)
            comparison = compare_systems(baseline, system, draws, config, store)
            _print_comparison(comparison)
        return 0

    if args.command == "run-tournament":
        champion_path = args.champion
        roster_glob = args.roster_glob
        if champion_path is None and config.tournament is not None:
            champion_path = config.tournament.champion
        if roster_glob is None and config.tournament is not None:
            roster_glob = config.tournament.roster_glob
        if champion_path is None:
            print(
                "error: --champion is required (or set tournament.champion in config)",
                file=sys.stderr,
            )
            return 1
        challenger_paths = resolve_roster(
            champion=champion_path,
            explicit=args.challengers,
            roster_glob=roster_glob,
            root=config.source_path.resolve().parent.parent,
        )
        if not challenger_paths and not args.challengers and roster_glob is None:
            print(
                "error: provide --challengers and/or --roster-glob "
                "(or set tournament.roster_glob in config)",
                file=sys.stderr,
            )
            return 1
        if not challenger_paths:
            print("error: no challengers resolved after excluding champion", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            champion = _load_system(champion_path, rules, name=champion_path.stem)
            challengers = [
                (path, _load_system(path, rules, name=path.stem))
                for path in challenger_paths
            ]
        except (KeyError, TypeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        store = ExperimentStore(config.paths.experiments_db)
        summary = run_ladder(
            champion=champion,
            champion_path=champion_path,
            challengers=challengers,
            draws=draws,
            config=config,
            store=store,
        )
        print(format_tournament_report(summary))
        if args.update_ratings:
            try:
                scoring = require_scoring(config)
            except ConfigError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            ratings = RatingsStore(
                scoring.elo.ratings_db,
                initial_rating=scoring.elo.initial_rating,
            )
            for duel in summary.duels:
                update = ratings.apply_duel(
                    baseline_id=duel.baseline_name,
                    challenger_id=duel.challenger_name,
                    decision=duel.decision,
                    k_factor=scoring.elo.k_factor,
                )
                print(
                    f"Elo duel {update.challenger_id} vs {update.baseline_id}: "
                    f"{update.decision} "
                    f"({update.challenger_before:.2f}->{update.challenger_after:.2f})"
                )
        if args.output is not None:
            write_tournament_summary(args.output, summary)
            print(f"Wrote tournament summary: {args.output}")
        return 0

    if args.command == "score-system":
        try:
            scoring = require_scoring(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            window_draws, contest_range = _select_window(
                draws, config.evaluation.validation_ratio, args.window
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        system = _load_system(args.system_file, rules, name=args.system_file.stem)
        result = compute_atlas_score(
            system,
            window_draws,
            weights=scoring.weights,
            min_hits=config.evaluation.primary_metric_min_hits,
        )
        print(
            format_score_report(
                result,
                system_name=system.name,
                window=args.window,
                contest_range=contest_range,
            )
        )
        return 0

    if args.command == "score-aci":
        try:
            scoring = require_scoring(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            draws = _evaluation_draws(config, rules)
        except ImportValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            window_draws, _contest_range = _select_window(
                draws, config.evaluation.validation_ratio, args.window
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        system = _load_system(args.system_file, rules, name=args.system_file.stem)
        min_hits = config.evaluation.primary_metric_min_hits
        if args.baseline is not None:
            baseline = _load_system(args.baseline, rules, name=args.baseline.stem)
            result = compute_pairwise_aci(
                baseline,
                system,
                window_draws,
                weights=scoring.weights,
                min_hits=min_hits,
                aci=scoring.aci,
            )
            print(
                format_aci_report(
                    result,
                    system_name=system.name,
                    baseline_name=baseline.name,
                    window=args.window,
                )
            )
        else:
            result = compute_aci(
                system,
                window_draws,
                weights=scoring.weights,
                min_hits=min_hits,
                aci=scoring.aci,
            )
            print(
                format_aci_report(
                    result, system_name=system.name, window=args.window
                )
            )
        return 0

    if args.command == "show-ratings":
        try:
            scoring = require_scoring(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        ratings = RatingsStore(
            scoring.elo.ratings_db,
            initial_rating=scoring.elo.initial_rating,
        )
        print(format_ratings_report(ratings.list_ratings()))
        return 0

    if args.command == "update-ratings":
        try:
            scoring = require_scoring(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        ratings = RatingsStore(
            scoring.elo.ratings_db,
            initial_rating=scoring.elo.initial_rating,
        )
        update = ratings.apply_duel(
            baseline_id=args.baseline_id,
            challenger_id=args.challenger_id,
            decision=args.decision,
            k_factor=scoring.elo.k_factor,
        )
        print(
            "ATLAS Elo update — historical duel ranking only; "
            "does not predict the next draw."
        )
        print(
            f"{update.baseline_id}: {update.baseline_before:.2f} -> {update.baseline_after:.2f}"
        )
        print(
            f"{update.challenger_id}: {update.challenger_before:.2f} -> {update.challenger_after:.2f}"
            f" ({update.decision})"
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _evaluation_draws(config, rules):
    return load_draws_for_evaluation(
        config.paths.raw_db,
        rules,
        min_contest=config.evaluation.min_contest,
        validation_ratio=config.evaluation.validation_ratio,
        n_folds=config.evaluation.freeze_policy.n_folds,
    )


def _select_window(draws, validation_ratio: float, window: str):
    train, holdout = split_train_validation(draws, validation_ratio)
    if window == "all":
        selected = list(draws)
    elif window == "train":
        selected = list(train)
    else:
        selected = list(holdout)
    if not selected:
        raise ValueError(f"Selected window {window!r} is empty")
    return selected, (selected[0].contest, selected[-1].contest)


def _print_comparison(comparison) -> None:
    print(
        "ATLAS strategy comparison with walk-forward freeze policy "
        "(not a prediction of future draws)."
    )
    print(
        f"Holdout diagnostic contests: "
        f"{comparison.validation_start}–{comparison.validation_end}"
    )
    print(
        f"Holdout metric (>=3 hits): baseline={comparison.baseline_metric} "
        f"candidate={comparison.candidate_metric} delta={comparison.delta} "
        f"({comparison.outcome})"
    )
    print(
        f"Walk-forward fold passes: {comparison.fold_passes}/{len(comparison.folds)} "
        f"(required {comparison.required_fold_passes}, "
        f"min_absolute_delta={comparison.min_absolute_delta})"
    )
    for fold in comparison.folds:
        status = "pass" if fold.passed else "fail"
        print(
            f"  fold {fold.fold_index} contests {fold.contest_start}–{fold.contest_end}: "
            f"delta={fold.delta} [{status}]"
        )
    if comparison.bootstrap is not None:
        boot = comparison.bootstrap
        print(
            f"Bootstrap CI mean_delta={boot.mean_delta:.3f} "
            f"[{boot.ci_lower:.3f}, {boot.ci_upper:.3f}] "
            f"(level={boot.ci_level}, seed={boot.seed})"
        )
    print(
        f"Decision: {comparison.decision} "
        f"(policy={comparison.freeze_policy_version})"
    )
    print(f"Experiment id: {comparison.experiment.id}")


def _load_system(path: Path, rules: LotteryRules, name: str) -> TicketSystem:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if "tickets" not in payload:
            raise ValueError(
                f"{path} is not a ticket-system JSON (missing 'tickets' key); "
                "exclude summaries/baselines from --roster-glob or --challengers"
            )
        tickets_raw = payload["tickets"]
        name = str(payload.get("name", name))
    else:
        tickets_raw = payload
    tickets = [Ticket.create(numbers, rules) for numbers in tickets_raw]
    return TicketSystem.create(tickets, rules, name=name)


def _write_system(path: Path, system: TicketSystem) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": system.name, "tickets": system.as_number_lists()}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
