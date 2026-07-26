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
from atlas.config import ConfigError, load_config, require_analytics, require_optimizer
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.comparison import compare_systems
from atlas.evaluation.evaluator import evaluate_system, format_evaluation_report
from atlas.evaluation.split import split_train_validation
from atlas.infrastructure.draw_repository import import_history, load_draws
from atlas.infrastructure.experiment_store import ExperimentStore
from atlas.optimization import (
    CoveringOptimizer,
    EnsembleOptimizer,
    EnsemblePoolError,
    GreedyOptimizer,
    LocalSearchOptimizer,
    covered_pair_count,
    format_covering_report,
    format_ensemble_report,
    format_local_search_report,
    format_optimize_report,
)
from atlas.optimization.ensemble import draft_from_pool, pool_tickets_from_files
from atlas.optimization.local_search import pair_coverage_count, primary_metric_count
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
        draws = load_draws(config.paths.raw_db, rules)
        system = _load_system(args.system_file, rules, name=args.system_file.stem)
        result = evaluate_system(system, draws, rules, config.prizes)
        print(format_evaluation_report(result, system.name))
        return 0

    if args.command == "compare-systems":
        draws = load_draws(config.paths.raw_db, rules)
        baseline = _load_system(args.baseline_file, rules, name=args.baseline_file.stem)
        candidate = _load_system(args.candidate_file, rules, name=args.candidate_file.stem)
        store = ExperimentStore(config.paths.experiments_db)
        comparison = compare_systems(baseline, candidate, draws, config, store)
        _print_comparison(comparison)
        return 0

    if args.command == "list-experiments":
        store = ExperimentStore(config.paths.experiments_db)
        experiments = store.list_experiments()
        if not experiments:
            print("No experiments recorded.")
            return 0
        for experiment in experiments:
            print(
                f"#{experiment.id} {experiment.timestamp} "
                f"{experiment.baseline_name}->{experiment.candidate_name} "
                f"delta={experiment.delta} decision={experiment.decision}"
            )
        return 0

    if args.command == "build-analytics":
        try:
            analytics = require_analytics(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
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
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
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
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
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
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
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

    if args.command == "optimize-ensemble":
        try:
            optimizer_settings = require_optimizer(config)
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if not optimizer_settings.ensemble.enabled:
            print("error: optimizer.ensemble.enabled is false", file=sys.stderr)
            return 1
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
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
        draws = load_draws(config.paths.raw_db, rules)
        if not draws:
            print("error: no draws available; run import-history first", file=sys.stderr)
            return 1
        champion = _load_system(champion_path, rules, name=champion_path.stem)
        challengers = [
            (path, _load_system(path, rules, name=path.stem)) for path in challenger_paths
        ]
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
        if args.output is not None:
            write_tournament_summary(args.output, summary)
            print(f"Wrote tournament summary: {args.output}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


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
