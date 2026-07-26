## Why

Covering is the current freeze-policy champion, but config tweaks (regenerate after new draws, `uniform` pair weight, larger greedy pools) failed to dethrone it. Cheap search variants are exhausted; the next leverage is a **local-search polish** that starts from the covering constructive solution and tries small ticket edits on the train window only, then competes under the same freeze policy.

## What Changes

- Add a third `OptimizationStrategy`: local search seeded from covering (or an optional provided system), improving a train-only objective via deterministic neighborhood moves.
- Add `optimizer.local_search` config (enabled, iteration/budget knobs, seed reuse) without changing freeze-policy semantics.
- Add CLI `optimize-local` (train-only optimize, JSON export, optional `--compare-baseline`).
- Keep covering/greedy available unchanged so the champion file can stay the baseline for challenges.
- Out of scope: genetic algorithms, tournament engine, changing accept rules, peeking at holdout/validation inside search, OR-Tools/MIP solvers.

## Capabilities

### New Capabilities
- `local-search-optimizer`: Seed from covering (or input system), apply deterministic local moves on train-only objectives, export a comparison candidate.

### Modified Capabilities
- `config-manager`: Load `optimizer.local_search` settings and reject invalid values clearly.
- `optimization-strategy`: Clarify that strategies MAY compose (seed from another strategy) while still consuming only the provided draw set.

## Impact

- New module under `atlas/optimization/` (e.g. `local_search.py`) plus config/CLI/tests.
- Reuses covering construction, pair helpers, evaluate/compare/freeze policy unchanged.
- Experiment log continues to record pairwise accept/reject vs champion.
