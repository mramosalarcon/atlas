## Why

`evaluation.min_contest` already filters evaluate/optimize/compare/tournament/score, but analytics still rebuild on full history and experiment logs do not store the floor explicitly. Operators comparing modern-window strategies against analytics or old experiment rows can misread diagnostics and cannot audit which contest window produced a decision.

## What Changes

- Apply `evaluation.min_contest` when building and showing analytics (number profiles, pairs, draw baseline) so diagnostics match the evaluation contest window when a floor is set.
- Persist `min_contest` on each experiment record (null when no floor) and surface it in list/retrieve paths.
- Keep `import-history` on full CSV/raw DB; do not truncate source history.
- Note the applied floor in analytics rebuild output when set.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `number-analytics`: Build/show number profiles over draws filtered by `min_contest` when configured.
- `coappearance-matrix`: Build/show pair co-appearance over the same filtered draw window.
- `draw-baseline`: Build/show draw-shape baselines over the same filtered draw window.
- `strategy-comparison`: Persist and retrieve `min_contest` on experiment records for each comparison.

## Impact

- CLI `build-analytics` / show-* paths; analytics store contents after rebuild (operators must rebuild after enabling/changing floor).
- `ExperimentStore` schema + comparison append/list; existing rows without the field remain readable (null/absent = unknown/pre-floor).
- Tests for filtered analytics and experiment persistence; no change to freeze thresholds or optimizer search logic.
