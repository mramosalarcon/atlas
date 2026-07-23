## Why

ATLAS has a single optimizer (greedy random-candidate pair coverage). A second algorithm is needed so candidates can compete under the same train-only search contract and walk-forward freeze policy. A **covering-design** optimizer is the natural next step: it constructs tickets more systematically to cover high-value pairs (optionally weighted by train co-appearance), rather than sampling a random candidate pool.

## What Changes

- Implement `CoveringOptimizer` behind the existing `OptimizationStrategy` interface.
- Build each ticket by greedily selecting numbers that maximize coverage of still-uncovered priority pairs (priority = uniform or train-frequency weights).
- Keep search on the caller-provided draw set only (train window); never touch validation inside the strategy.
- Add `optimizer.covering` config (`enabled`, `pair_weight` mode) alongside existing greedy settings; reuse shared `seed` for deterministic tie-breaking.
- Add CLI `optimize-covering` (export JSON + optional `--compare-baseline` via existing freeze policy).
- Out of scope: genetic/annealing/monte-carlo, tournament ranking UI, triple/quad covering as primary objective, OR-Tools.

## Capabilities

### New Capabilities
- `covering-optimizer`: Deterministic covering-design construction of an 8-ticket system prioritizing uncovered pairs.

### Modified Capabilities
- `config-manager`: Add covering optimizer settings under `optimizer.covering`.

## Impact

- Extends `atlas/optimization/` with `covering.py` (reuses `pairs.py` helpers).
- Extends config settings/loader and CLI.
- Reuses evaluation/compare/freeze-policy unchanged.
- Enables fair A/B of greedy vs covering under walk-forward accepts.
