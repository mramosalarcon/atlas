## ADDED Requirements

### Requirement: Local-search objective includes higher-order coverage tie-breaks
The system SHALL rank local-search candidate systems by lexicographic train objective `(primary_metric_count, pair_coverage, triple_coverage, quad_coverage)` when deciding whether to accept a move, using only the provided draw set for the primary metric.

#### Scenario: Triple coverage breaks a pair tie
- **WHEN** two neighboring systems have equal primary-metric count and equal pair coverage, and one has strictly greater triple coverage
- **THEN** local search prefers the system with greater triple coverage

#### Scenario: Quad coverage breaks a triple tie
- **WHEN** two neighboring systems tie on primary metric, pairs, and triples, and one has strictly greater quad coverage
- **THEN** local search prefers the system with greater quad coverage

### Requirement: Local-search report includes higher-order coverage
The system SHALL include triple and quad coverage counts in the local-search optimize report while remaining a non-predictive comparison candidate.

#### Scenario: Report lists triple and quad coverage
- **WHEN** a local-search optimize report is produced
- **THEN** it includes unordered triple and quad coverage counts and states the system does not predict the next draw
