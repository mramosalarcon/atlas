## 1. Config

- [x] 1.1 Add `optimizer.covering` to `config/config.yaml` (`enabled`, `pair_weight: train_frequency`)
- [x] 1.2 Extend typed settings + loader for covering settings; reject unsupported `pair_weight`
- [x] 1.3 Add config tests for covering defaults and invalid pair_weight

## 2. Covering strategy

- [x] 2.1 Build pair priority list for `uniform` and `train_frequency` modes from the provided draw set / number range
- [x] 2.2 Implement constructive ticket growth from priority uncovered pairs with deterministic tie-breaks
- [x] 2.3 Implement `CoveringOptimizer` as `OptimizationStrategy` producing a full `TicketSystem`
- [x] 2.4 Add unit tests for seeding from top pair, determinism, and train_frequency ordering
- [x] 2.5 Format covering optimize report as comparison-candidate only (non-predictive)

## 3. CLI and smoke

- [x] 3.1 Add `optimize-covering` CLI: train-only optimize, JSON export, optional `--compare-baseline`
- [x] 3.2 Smoke on Melate history; optionally compare covering vs baseline/greedy under freeze policy; confirm pytest passes
