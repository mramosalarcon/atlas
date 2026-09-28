## ADDED Requirements

### Requirement: Experiment records persist min_contest
The system SHALL store the configured `evaluation.min_contest` value with each comparison experiment (`null` when no floor is configured) and SHALL expose that value when experiments are listed or retrieved.

#### Scenario: Floor stored when configured
- **WHEN** compare-systems completes with `evaluation.min_contest=2088`
- **THEN** the experiment record stores `min_contest=2088`

#### Scenario: Absent floor stored as null
- **WHEN** compare-systems completes with no `min_contest` configured
- **THEN** the experiment record stores a null/absent `min_contest`

#### Scenario: Listed experiments show stored floor
- **WHEN** list-experiments runs after a comparison that stored `min_contest=2088`
- **THEN** the listed entry for that experiment includes `2088` as the contest floor
