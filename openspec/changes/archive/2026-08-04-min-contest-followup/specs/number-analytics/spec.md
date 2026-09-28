## ADDED Requirements

### Requirement: Number analytics honor the evaluation contest floor
When `evaluation.min_contest` is set, the system SHALL compute number profiles only from draws with contests `>= min_contest`, without modifying the raw history database.

#### Scenario: Profiles use filtered draws
- **WHEN** build-analytics runs with `min_contest=2088` and the raw database contains contests below and above 2088
- **THEN** number profiles are computed only from contests `>= 2088`

#### Scenario: Empty filtered window fails clearly
- **WHEN** build-analytics would run but no contests satisfy `min_contest`
- **THEN** the command fails with an error naming `min_contest` and does not write success analytics
