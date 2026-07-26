## ADDED Requirements

### Requirement: Default Melate bootstrap gate uses non-negative CI lower bound
When using the shipped Melate freeze-policy defaults with bootstrap enabled, the system SHALL use `min_ci_lower` of 0 so accept requires the bootstrap CI lower bound on mean fold-delta to be at least zero, unless an operator overrides the value in config.

#### Scenario: Default min_ci_lower is zero
- **WHEN** shipped Melate config is loaded
- **THEN** `evaluation.freeze_policy.bootstrap.min_ci_lower` equals 0

### Requirement: Operators may disable bootstrap without code changes
The system SHALL allow operators to set `bootstrap.enabled` to false in YAML to skip the bootstrap gate while retaining walk-forward fold requirements.

#### Scenario: Explicit disable skips bootstrap gate
- **WHEN** config sets `bootstrap.enabled` to false
- **THEN** comparison accept/reject does not require a bootstrap CI check
