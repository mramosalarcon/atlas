## Why

Melate’s number pool expanded over time; early contests lack or underuse balls in the upper band (especially 52–56). Optimizers and freeze folds that train on full history therefore bias toward 1–39 and reject high-band challengers even when they fit the modern game. Operators need a configurable contest floor (default Melate cut **2088**) so candidate search and comparison run on the modern full-pool era without deleting the raw CSV.

## What Changes

- Add optional `evaluation.min_contest` to config (ship Melate default `2088`).
- Filter draws used for evaluate / optimize / compare / tournament / Atlas Score–ACI to contests `>= min_contest`.
- Keep CSV import and the raw SQLite history intact (no destructive cut of source data).
- Fail clearly when the filtered window is empty or too small for train/validation/freeze folds.
- Document that champions crowned under the filtered window are not comparable 1:1 to prior full-history champions.

## Capabilities

### New Capabilities

- _(none)_

### Modified Capabilities

- `config-manager`: Load and validate optional `evaluation.min_contest`.
- `draw-import`: Loading draws for evaluation workflows SHALL support contest-floor filtering without changing import semantics (CSV → full raw DB unchanged).
- `system-evaluation`: Evaluation over history uses the configured contest window when `min_contest` is set.
- `walk-forward-evaluation`: Walk-forward folds are computed on the filtered draw sequence.
- `strategy-comparison`: Compare/holdout diagnostics use the filtered window.

## Impact

- `config/config.yaml`, `atlas/config/settings.py`, `atlas/config/loader.py`
- `atlas/infrastructure/draw_repository.py` and/or a shared draw-window helper
- CLI paths that call `load_draws` for eval/optimize/compare/tournament/score
- Tests for filter bounds, defaults, and insufficient-window errors
- Operators should regenerate candidates and re-run tournament after enabling the floor
