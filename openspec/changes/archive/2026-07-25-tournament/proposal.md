## Why

ATLAS can compare one baseline vs one candidate under freeze policy, but operators still run ad-hoc CLI duels by hand. With greedy, covering, local-search, and hand systems in play, we need a **tournament** that schedules challenges, promotes a living champion only on freeze `accepted`, and prints a durable summary—without inventing a new truth oracle.

## What Changes

- Add a ladder tournament runner: fixed champion + roster of challenger system JSON files; each challenger faces the current champion once via existing freeze-policy compare.
- Promote the champion only when a challenger is `accepted`; rejected challengers leave the champion unchanged.
- Persist each duel through the existing experiment log; emit a tournament summary (roster, schedule, outcomes, final champion) to stdout and optional JSON under `data/exports/`.
- Add CLI `run-tournament` (champion path, challenger paths or directory, optional output report path).
- Optional config defaults for champion path / roster globs (non-breaking).
- Out of scope: Swiss/knockout brackets, auto-regenerating optimizers mid-tournament, dashboard UI, changing freeze-policy rules, round-robin matrix (defer), ensemble ticket drafting.

## Capabilities

### New Capabilities
- `strategy-tournament`: Ladder scheduling, champion promotion on freeze accept, and tournament summary reporting.

### Modified Capabilities
- `config-manager`: Optional tournament defaults (champion path, roster glob) when present in YAML.

## Impact

- New package area (e.g. `atlas/tournament/` or under `atlas/evaluation/`) composing `compare_systems` / `ExperimentStore`.
- CLI extension; config settings/loader if defaults are added.
- Reuses evaluation, freeze policy, and experiment store unchanged as the sole judge.
