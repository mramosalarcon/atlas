"""Ladder tournament orchestration over freeze-policy compares."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
from typing import Callable, Sequence

from atlas.config.settings import AppConfig
from atlas.domain.draw import Draw
from atlas.domain.ticket_system import TicketSystem
from atlas.evaluation.comparison import ComparisonResult, compare_systems
from atlas.infrastructure.experiment_store import ExperimentStore

CompareFn = Callable[
    [TicketSystem, TicketSystem, Sequence[Draw], AppConfig, ExperimentStore],
    ComparisonResult,
]


@dataclass(frozen=True)
class DuelResult:
    challenger_path: str
    challenger_name: str
    baseline_name: str
    decision: str
    fold_passes: int
    required_fold_passes: int
    holdout_delta: int
    experiment_id: int
    promoted: bool


@dataclass(frozen=True)
class TournamentSummary:
    tournament_id: str
    initial_champion_path: str
    initial_champion_name: str
    final_champion_path: str
    final_champion_name: str
    challenger_paths: tuple[str, ...]
    duels: tuple[DuelResult, ...]

    def to_dict(self) -> dict:
        return {
            "tournament_id": self.tournament_id,
            "initial_champion_path": self.initial_champion_path,
            "initial_champion_name": self.initial_champion_name,
            "final_champion_path": self.final_champion_path,
            "final_champion_name": self.final_champion_name,
            "challenger_paths": list(self.challenger_paths),
            "duels": [asdict(duel) for duel in self.duels],
        }


def resolve_roster(
    *,
    champion: Path,
    explicit: Sequence[Path] | None = None,
    roster_glob: str | None = None,
    root: Path | None = None,
) -> list[Path]:
    champion_resolved = champion.resolve()
    paths: list[Path] = []
    seen: set[Path] = set()

    for path in explicit or []:
        resolved = path.resolve()
        if resolved == champion_resolved:
            continue
        if resolved not in seen:
            seen.add(resolved)
            paths.append(resolved)

    if roster_glob:
        pattern = roster_glob
        if root is not None and not Path(roster_glob).is_absolute():
            pattern = str(root / roster_glob)
        for match in sorted(glob(pattern)):
            resolved = Path(match).resolve()
            if resolved == champion_resolved:
                continue
            if resolved.name.startswith("sample_"):
                continue
            if resolved not in seen:
                seen.add(resolved)
                paths.append(resolved)

    return paths


def make_tournament_id(now: datetime | None = None) -> str:
    stamp = now or datetime.now(timezone.utc)
    return stamp.strftime("%Y%m%dT%H%M%SZ")


def run_ladder(
    *,
    champion: TicketSystem,
    champion_path: Path,
    challengers: Sequence[tuple[Path, TicketSystem]],
    draws: Sequence[Draw],
    config: AppConfig,
    store: ExperimentStore,
    compare_fn: CompareFn | None = None,
    tournament_id: str | None = None,
) -> TournamentSummary:
    compare = compare_fn or compare_systems
    tid = tournament_id or make_tournament_id()
    current = champion
    current_path = champion_path.resolve()
    duels: list[DuelResult] = []

    for path, challenger in challengers:
        result = compare(current, challenger, draws, config, store)
        promoted = result.decision == "accepted"
        duels.append(
            DuelResult(
                challenger_path=str(path.resolve()),
                challenger_name=challenger.name,
                baseline_name=current.name,
                decision=result.decision,
                fold_passes=result.fold_passes,
                required_fold_passes=result.required_fold_passes,
                holdout_delta=result.delta,
                experiment_id=result.experiment.id,
                promoted=promoted,
            )
        )
        if promoted:
            current = challenger
            current_path = path.resolve()

    return TournamentSummary(
        tournament_id=tid,
        initial_champion_path=str(champion_path.resolve()),
        initial_champion_name=champion.name,
        final_champion_path=str(current_path),
        final_champion_name=current.name,
        challenger_paths=tuple(str(path.resolve()) for path, _ in challengers),
        duels=tuple(duels),
    )


def format_tournament_report(summary: TournamentSummary) -> str:
    lines = [
        "ATLAS ladder tournament — historical freeze-policy comparison only; "
        "does not predict the next draw.",
        f"Tournament id: {summary.tournament_id}",
        f"Initial champion: {summary.initial_champion_name} ({summary.initial_champion_path})",
        f"Challengers ({len(summary.challenger_paths)}):",
    ]
    for path in summary.challenger_paths:
        lines.append(f"  - {path}")
    lines.append("Duels:")
    for idx, duel in enumerate(summary.duels, start=1):
        promo = "promoted" if duel.promoted else "retained"
        lines.append(
            f"  {idx}. {duel.baseline_name} <- {duel.challenger_name}: "
            f"{duel.decision} "
            f"(folds {duel.fold_passes}/{duel.required_fold_passes}, "
            f"holdout_delta={duel.holdout_delta}, experiment=#{duel.experiment_id}) "
            f"[{promo}]"
        )
    lines.append(
        f"Final champion: {summary.final_champion_name} ({summary.final_champion_path})"
    )
    return "\n".join(lines) + "\n"


def write_tournament_summary(path: Path, summary: TournamentSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8")
