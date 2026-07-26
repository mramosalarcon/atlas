"""Tournament ladder tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket import Ticket
from atlas.domain.ticket_system import TicketSystem
from atlas.tournament.ladder import (
    format_tournament_report,
    resolve_roster,
    run_ladder,
    write_tournament_summary,
)


def _system(name: str, rules: LotteryRules) -> TicketSystem:
    # Distinct enough tickets for uniqueness; content unused by fake compare.
    base = {
        "a": [[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 7], [1, 2, 3, 4, 5, 8],
              [1, 2, 3, 4, 5, 9], [1, 2, 3, 4, 5, 10], [1, 2, 3, 4, 5, 11],
              [1, 2, 3, 4, 5, 12], [1, 2, 3, 4, 5, 13]],
        "b": [[2, 3, 4, 5, 6, 7], [2, 3, 4, 5, 6, 8], [2, 3, 4, 5, 6, 9],
              [2, 3, 4, 5, 6, 10], [2, 3, 4, 5, 6, 11], [2, 3, 4, 5, 6, 12],
              [2, 3, 4, 5, 6, 13], [2, 3, 4, 5, 6, 14]],
        "c": [[3, 4, 5, 6, 7, 8], [3, 4, 5, 6, 7, 9], [3, 4, 5, 6, 7, 10],
              [3, 4, 5, 6, 7, 11], [3, 4, 5, 6, 7, 12], [3, 4, 5, 6, 7, 13],
              [3, 4, 5, 6, 7, 14], [3, 4, 5, 6, 7, 15]],
    }[name]
    tickets = [Ticket.create(nums, rules) for nums in base]
    return TicketSystem.create(tickets, rules, name=name)


@dataclass
class _FakeExperiment:
    id: int


def test_resolve_roster_excludes_champion_and_samples(tmp_path: Path) -> None:
    champ = tmp_path / "champ.json"
    a = tmp_path / "a_candidate.json"
    b = tmp_path / "b_candidate.json"
    sample = tmp_path / "sample_candidate.json"
    for path in (champ, a, b, sample):
        path.write_text("{}", encoding="utf-8")

    roster = resolve_roster(
        champion=champ,
        explicit=[a],
        roster_glob=str(tmp_path / "*_candidate.json"),
    )
    assert a.resolve() in roster
    assert b.resolve() in roster
    assert champ.resolve() not in roster
    assert sample.resolve() not in roster
    assert roster == sorted(roster)


def test_ladder_promotes_on_accept_and_counts_duels(tmp_path: Path) -> None:
    rules = LotteryRules(1, 56, 6, True, 8)
    champ = _system("a", rules)
    winner = _system("b", rules)
    loser = _system("c", rules)
    champ_path = tmp_path / "a.json"
    winner_path = tmp_path / "b.json"
    loser_path = tmp_path / "c.json"

    calls: list[tuple[str, str]] = []
    experiment_ids = iter([10, 11])

    def fake_compare(baseline, candidate, draws, config, store):
        calls.append((baseline.name, candidate.name))
        decision = "accepted" if candidate.name == "b" else "rejected"
        return SimpleNamespace(
            decision=decision,
            fold_passes=4 if decision == "accepted" else 1,
            required_fold_passes=4,
            delta=1 if decision == "accepted" else -1,
            experiment=_FakeExperiment(id=next(experiment_ids)),
        )

    summary = run_ladder(
        champion=champ,
        champion_path=champ_path,
        challengers=[(winner_path, winner), (loser_path, loser)],
        draws=[],
        config=SimpleNamespace(),  # type: ignore[arg-type]
        store=SimpleNamespace(),  # type: ignore[arg-type]
        compare_fn=fake_compare,
        tournament_id="test-id",
    )

    assert len(summary.duels) == 2
    assert calls == [("a", "b"), ("b", "c")]
    assert summary.duels[0].promoted is True
    assert summary.duels[1].promoted is False
    assert summary.final_champion_name == "b"
    assert summary.final_champion_path == str(winner_path.resolve())


def test_ladder_retains_champion_on_reject(tmp_path: Path) -> None:
    rules = LotteryRules(1, 56, 6, True, 8)
    champ = _system("a", rules)
    challenger = _system("c", rules)

    def fake_compare(baseline, candidate, draws, config, store):
        return SimpleNamespace(
            decision="rejected",
            fold_passes=0,
            required_fold_passes=4,
            delta=-5,
            experiment=_FakeExperiment(id=1),
        )

    summary = run_ladder(
        champion=champ,
        champion_path=tmp_path / "a.json",
        challengers=[(tmp_path / "c.json", challenger)],
        draws=[],
        config=SimpleNamespace(),  # type: ignore[arg-type]
        store=SimpleNamespace(),  # type: ignore[arg-type]
        compare_fn=fake_compare,
        tournament_id="t2",
    )
    assert summary.final_champion_name == "a"
    assert summary.duels[0].promoted is False


def test_tournament_report_non_predictive(tmp_path: Path) -> None:
    rules = LotteryRules(1, 56, 6, True, 8)
    champ = _system("a", rules)

    def fake_compare(baseline, candidate, draws, config, store):
        return SimpleNamespace(
            decision="rejected",
            fold_passes=0,
            required_fold_passes=4,
            delta=0,
            experiment=_FakeExperiment(id=9),
        )

    summary = run_ladder(
        champion=champ,
        champion_path=tmp_path / "a.json",
        challengers=[(tmp_path / "c.json", _system("c", rules))],
        draws=[],
        config=SimpleNamespace(),  # type: ignore[arg-type]
        store=SimpleNamespace(),  # type: ignore[arg-type]
        compare_fn=fake_compare,
        tournament_id="t3",
    )
    report = format_tournament_report(summary).lower()
    assert "does not predict" in report
    out = tmp_path / "summary.json"
    write_tournament_summary(out, summary)
    assert out.is_file()
    assert "tournament_id" in out.read_text(encoding="utf-8")
