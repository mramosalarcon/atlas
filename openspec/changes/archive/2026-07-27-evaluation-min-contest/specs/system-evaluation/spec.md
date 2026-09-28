## ADDED Requirements

### Requirement: System evaluation uses the configured contest window
When `evaluation.min_contest` is set, the system SHALL evaluate ticket systems only against draws in that contest window (contests `>= min_contest`) for evaluation commands that load history from the raw database.

#### Scenario: Metrics reflect filtered history
- **WHEN** evaluate-system runs with `min_contest` set and filtered draws are non-empty
- **THEN** reported draws-evaluated equals the count of contests in the filtered window

#### Scenario: Empty filtered window fails clearly
- **WHEN** evaluate-system would load history but no contests satisfy `min_contest`
- **THEN** the command fails with an error naming `min_contest` and does not report success metrics
