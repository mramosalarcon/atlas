## Why

Under `evaluation.min_contest=2088`, the train-aggregate local-search champion still wins freeze policy while holdout-tuned hybrids look better on the last window and fail walk-forward folds. Operators want a different optimizer whose search objective matches freeze stability so a challenger can earn promotion with better fold-robust results—not by lowering the freeze bar.

## What Changes

- Add a fold-robust local-search optimizer that seeds from covering (same neighborhood as existing local search) but scores moves using chronological fold metrics on the provided train draws.
- Prefer worst-fold primary metric, then sum of fold primaries, then aggregate train primary and coverage tie-breaks (pairs → triples → quads).
- Add config + CLI (`optimize-fold-robust`) to export a comparison candidate; no auto-accept; freeze policy unchanged.
- Keep existing local-search / greedy / covering / ensemble behaviors available.

## Capabilities

### New Capabilities
- `fold-robust-optimizer`: Covering-seeded hill climb with walk-forward fold-robust train objective for Melate 8-ticket systems.

### Modified Capabilities
- `config-manager`: Load optional `optimizer.fold_robust` settings (enabled, max_passes, primary_metric_min_hits).
- `optimization-strategy`: Register fold-robust as an available optimization strategy alongside existing ones.

## Impact

- New module under `atlas/optimization/` (or extension of local-search helpers), CLI command, config YAML/settings/loader, unit tests, and operator smoke via optimize + compare/tournament against current champion.
- Reuses `partition_contiguous_folds` / freeze `n_folds` for train partitioning; must not read validation/holdout during search.
- Freeze policy, tournament rules, and `min_contest` behavior unchanged.
