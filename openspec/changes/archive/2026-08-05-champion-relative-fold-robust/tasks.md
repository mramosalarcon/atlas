## 1. Config

- [x] 1.1 Add `optimizer.fold_robust.objective` (`absolute`|`relative`, default absolute) and optional `relative_to` path to settings/loader; reject invalid objective values
- [x] 1.2 Config tests: omit → absolute; relative + relative_to loaded; invalid objective fails at load

## 2. Optimizer + CLI

- [x] 2.1 Implement relative score (fold deltas vs baseline; pass count using `evaluation.min_absolute_delta`; then sum deltas; then absolute tie-breakers) and wire into hill climb
- [x] 2.2 Resolve baseline path (`--relative-to` → config `relative_to` → `seed_from` → `tournament.champion`); fail clearly when relative mode lacks a baseline
- [x] 2.3 CLI: `--objective` and `--relative-to`; report mode, baseline, per-fold train deltas, train fold-pass count
- [x] 2.4 Unit tests: absolute unchanged; relative prefers extra fold pass; missing baseline errors; determinism with fixed baseline

## 3. Smoke

- [x] 3.1 Smoke: relative fold-robust seeded from champion vs champion baseline; confirm report diagnostics and train contests `>= min_contest`
- [x] 3.2 Smoke: `--compare-baseline` vs champion; record fold-pass outcome (promotion not required)
- [x] 3.3 Confirm pytest passes
