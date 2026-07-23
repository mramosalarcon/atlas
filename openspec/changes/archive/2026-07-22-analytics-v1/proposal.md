## Why

ATLAS Core can evaluate and compare 8-ticket systems, but operators still lack descriptive statistics over the Melate history (per-number profiles, pair co-appearance, baseline draw shape). Without that layer, strategy design stays opaque and later scoring/optimization would invent metrics ad hoc. Analytics v1 adds reproducible, config-driven diagnostics that never claim to predict the next draw.

## What Changes

- Compute per-number profiles over a configurable draw window: total frequency, rolling windows (e.g. 10/20/50/100), recency (contests since last appearance), and additional-number appearances.
- Build a symmetric co-appearance matrix for main-number pairs (and expose top pairs).
- Compute historical baseline descriptors for draws (sum distribution summary, odd/even counts, decade occupancy, consecutive-pair rates) as reference only.
- Persist analytics outputs to a separate processed store (not the immutable raw DB).
- Add CLI commands to build analytics and inspect number/pair reports with explicit non-prediction language.
- Extend `config.yaml` with analytics windows and output paths.
- Explicitly out of scope: Atlas Score / ELO rating, community detection, optimizers, strategy auto-adoption, dashboard.

## Capabilities

### New Capabilities
- `number-analytics`: Per-number historical profiles (frequency, rolling counts, recency, additional appearances) over configurable windows.
- `coappearance-matrix`: Pair co-appearance counts/rates from main numbers and top-pair reporting.
- `draw-baseline`: Aggregate descriptive baselines of draw shape over history (sum, parity, decades, consecutives).

### Modified Capabilities
- `config-manager`: Add analytics window sizes, analytics DB/export paths, and related settings to external config.

## Impact

- Fills `atlas/analytics/` (currently empty); may add small helpers under `atlas/infrastructure/` for analytics persistence.
- Extends `atlas/config` settings/loader and `config/config.yaml`.
- Adds CLI subcommands (e.g. `build-analytics`, `show-number`, `show-pairs`, `show-baseline`).
- Depends on existing raw history import (`draw-import`) and does not change evaluation or freeze-policy semantics.
- Dependencies remain stdlib + PyYAML + pytest (no NetworkX/Pandas required for v1).
