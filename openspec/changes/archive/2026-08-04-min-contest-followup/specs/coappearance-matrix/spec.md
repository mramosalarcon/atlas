## ADDED Requirements

### Requirement: Pair co-appearance honors the evaluation contest floor
When `evaluation.min_contest` is set, the system SHALL build the main-number co-appearance matrix only from draws with contests `>= min_contest`.

#### Scenario: Pairs reflect filtered history
- **WHEN** build-analytics runs with `min_contest=2088`
- **THEN** pair co-appearance counts include only draws with `CONCURSO >= 2088`
