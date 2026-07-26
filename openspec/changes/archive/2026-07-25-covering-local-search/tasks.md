## 1. Config

- [x] 1.1 Add `optimizer.local_search` to `config/config.yaml` (`enabled`, `max_passes: 20`)
- [x] 1.2 Extend typed settings + loader for local-search settings; reject `max_passes < 1`
- [x] 1.3 Add config tests for local-search defaults and invalid max_passes

## 2. Local-search strategy

- [x] 2.1 Implement train primary-metric + pair-coverage scoring helpers on a provided draw set
- [x] 2.2 Implement lex-ordered single-number replacement neighborhood with duplicate-ticket rejection
- [x] 2.3 Implement first-improvement hill-climb seeded from `CoveringOptimizer` with `max_passes`
- [x] 2.4 Implement `LocalSearchOptimizer` as `OptimizationStrategy` producing a full `TicketSystem`
- [x] 2.5 Add unit tests for determinism, no-op when no improvement, and invalid duplicate moves skipped
- [x] 2.6 Format local-search optimize report as comparison-candidate only (non-predictive)

## 3. CLI and smoke

- [x] 3.1 Add `optimize-local` CLI: train-only optimize, JSON export, optional `--compare-baseline`
- [x] 3.2 Smoke vs `covering_candidate.json` under freeze policy; confirm pytest passes
