## 1. Config

- [x] 1.1 Add `optimizer.ensemble` to `config/config.yaml` (`enabled`, `seeds`, `sources: [greedy, covering]`)
- [x] 1.2 Extend typed settings + loader; reject empty seeds/sources and unsupported source names
- [x] 1.3 Add config tests for defaults and invalid ensemble settings

## 2. Ensemble pool and draft

- [x] 2.1 Implement unique ticket pooling from multi-seed greedy/covering runs on the provided draw set
- [x] 2.2 Implement file-source pooling from system JSON exports
- [x] 2.3 Implement deterministic draft by train primary-metric then pair coverage with clear insufficient-pool errors
- [x] 2.4 Implement `EnsembleOptimizer` as `OptimizationStrategy` producing a full `TicketSystem`
- [x] 2.5 Add unit tests for dedup, draft size, determinism, and insufficient pool
- [x] 2.6 Format ensemble optimize report as comparison-candidate only (non-predictive)

## 3. CLI and smoke

- [x] 3.1 Add `optimize-ensemble` CLI: train-only generate and/or `--sources` files, JSON export, optional `--compare-baseline`
- [x] 3.2 Smoke vs current champion (or tournament entry); confirm pytest passes
