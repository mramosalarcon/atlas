"""ATLAS command-line entrypoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas.config import ConfigError, load_config
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.comparison import compare_systems
from atlas.evaluation.evaluator import evaluate_system, format_evaluation_report
from atlas.infrastructure.draw_repository import import_history, load_draws
from atlas.infrastructure.experiment_store import ExperimentStore

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
        print(
            "ATLAS strategy comparison on historical validation window "
            "(not a prediction of future draws)."
        )
        print(
            f"Validation contests: {comparison.validation_start}–{comparison.validation_end}"
        )
        print(f"Baseline metric (>=3 hits): {comparison.baseline_metric}")
        print(f"Candidate metric (>=3 hits): {comparison.candidate_metric}")
        print(f"Delta: {comparison.delta}")
        print(f"Outcome: {comparison.outcome}")
        print(f"Decision: {comparison.decision} (threshold={comparison.min_absolute_delta})")
        print(f"Experiment id: {comparison.experiment.id}")
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

    parser.error(f"Unknown command: {args.command}")
    return 2


def _load_system(path: Path, rules: LotteryRules, name: str) -> TicketSystem:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        tickets_raw = payload["tickets"]
        name = str(payload.get("name", name))
    else:
        tickets_raw = payload
    tickets = [Ticket.create(numbers, rules) for numbers in tickets_raw]
    return TicketSystem.create(tickets, rules, name=name)


if __name__ == "__main__":
    raise SystemExit(main())
