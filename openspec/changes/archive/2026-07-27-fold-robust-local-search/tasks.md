## 1. Config

- [x] 1.1 Add `optimizer.fold_robust` to shipped `config/config.yaml` (enabled, max_passes, primary_metric_min_hits)
- [x] 1.2 Extend settings + loader for fold-robust (validate `max_passes >= 1`)
- [x] 1.3 Add config tests for defaults and invalid `max_passes`

## 2. Optimizer

- [x] 2.1 Implement fold-robust score using `partition_contiguous_folds` + lexicographic `(min_fold, sum_fold, total, pairs, triples, quads)`
- [x] 2.2 Implement `FoldRobustOptimizer` (covering seed, legal local-search moves, deterministic hill climb)
- [x] 2.3 Unit tests: determinism; prefer higher min-fold over aggregate-only gain; duplicate tickets rejected

## 3. CLI and operator smoke

- [x] 3.1 Add `optimize-fold-robust` CLI (train-only search, honors `min_contest`, optional `--compare-baseline`)
- [x] 3.2 Smoke: export candidate, confirm train contests `>= min_contest`, report fold-aware metrics
- [x] 3.3 Smoke: compare or tournament vs current champion; record fold-pass outcome (promotion not required)
- [x] 3.4 Confirm pytest passes
