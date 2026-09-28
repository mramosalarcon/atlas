## 1. Config

- [x] 1.1 Add optional `optimizer.fold_robust.seed_from` to settings/loader (null = covering); ship Melate default to champion export path
- [x] 1.2 Config tests: default path present; null/omit uses covering semantics; invalid missing file handled at optimize time (not load)

## 2. Optimizer + CLI

- [x] 2.1 Load seed TicketSystem from path when configured; else covering; fail clearly if file missing/invalid
- [x] 2.2 Add `optimize-fold-robust --seed-from` override; report seed source
- [x] 2.3 Unit tests: covering fallback; file seed used; deterministic for same seed file; missing path errors

## 3. Smoke

- [x] 3.1 Smoke: champion-seeded fold-robust export; confirm seed path in report and train contests `>= min_contest`
- [x] 3.2 Smoke: `--compare-baseline` vs champion; record fold-pass outcome (promotion not required)
- [x] 3.3 Confirm pytest passes
