## ADDED Requirements

### Requirement: Draw baseline honors the evaluation contest floor
When `evaluation.min_contest` is set, the system SHALL compute draw-shape baseline diagnostics only from draws with contests `>= min_contest`.

#### Scenario: Baseline reflects filtered history
- **WHEN** build-analytics runs with `min_contest=2088`
- **THEN** baseline descriptors are computed only from contests `>= 2088`
