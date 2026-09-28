## ADDED Requirements

### Requirement: Fold-robust objective mode is loaded from config
The system SHALL load `optimizer.fold_robust.objective` as `absolute` or `relative` (default `absolute` when omitted) and an optional `optimizer.fold_robust.relative_to` path (null/omit means fall back to seed_from then tournament.champion at optimize time).

#### Scenario: Default objective is absolute
- **WHEN** the application loads config that omits `optimizer.fold_robust.objective`
- **THEN** fold-robust objective resolves to `absolute`

#### Scenario: Relative mode and relative_to are exposed
- **WHEN** config sets `optimizer.fold_robust.objective` to `relative` and optionally `relative_to` to a path
- **THEN** those settings are available to the fold-robust optimizer

### Requirement: Invalid fold-robust objective fails clearly
The system SHALL fail configuration load with a clear error if `optimizer.fold_robust.objective` is not `absolute` or `relative`.

#### Scenario: Unknown objective value
- **WHEN** config sets `optimizer.fold_robust.objective` to a value other than `absolute` or `relative`
- **THEN** configuration load raises an error naming `objective`
