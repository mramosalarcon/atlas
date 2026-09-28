## ADDED Requirements

### Requirement: Strategy comparison uses the filtered contest window
When `evaluation.min_contest` is set, the system SHALL run freeze-policy comparison and holdout diagnostics on draws with contests `>= min_contest` only.

#### Scenario: Holdout diagnostic contests respect floor
- **WHEN** compare-systems runs with `min_contest=2088` and the filtered window is large enough to split
- **THEN** reported holdout diagnostic contest ids are all `>= 2088`

#### Scenario: Insufficient filtered draws fail clearly
- **WHEN** compare-systems runs but the filtered window cannot support the configured freeze folds or validation split
- **THEN** the command fails with a clear error referring to `min_contest` rather than producing a silent or partial decision
