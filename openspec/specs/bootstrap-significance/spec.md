## Purpose

Optional paired bootstrap over walk-forward fold deltas to gate freeze-policy accept decisions with a confidence interval.

## Requirements

### Requirement: Optional paired bootstrap of fold deltas
When bootstrap is enabled in config, the system SHALL run a seeded paired bootstrap over walk-forward fold deltas and compute a confidence interval for the mean delta.

#### Scenario: Reproducible bootstrap
- **WHEN** bootstrap is run twice with the same fold deltas, seed, resample count, and CI level
- **THEN** both runs produce identical CI bounds

#### Scenario: Bootstrap disabled skips computation
- **WHEN** bootstrap.enabled is false
- **THEN** comparison proceeds without bootstrap CI fields (or records them as null/absent)

### Requirement: Bootstrap gate when enabled
When bootstrap is enabled, the system SHALL require the configured CI lower bound to be ≥ `min_ci_lower` as a necessary condition for accept (in addition to walk-forward pass requirements).

#### Scenario: Reject when CI lower bound too low
- **WHEN** bootstrap is enabled and the CI lower bound is below `min_ci_lower`
- **THEN** the freeze decision is `rejected` even if fold-pass counts are otherwise sufficient
