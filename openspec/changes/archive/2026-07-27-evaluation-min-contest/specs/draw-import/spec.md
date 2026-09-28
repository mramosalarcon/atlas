## ADDED Requirements

### Requirement: Evaluation draw loads may filter by minimum contest
The system SHALL support loading draws from the raw SQLite database filtered to contests greater than or equal to a configured minimum contest id, without modifying the stored raw history or the source CSV.

#### Scenario: Filter excludes earlier contests
- **WHEN** draws are loaded for evaluation with `min_contest=2088` and the database contains contests below and above 2088
- **THEN** the returned draw list includes only contests with `CONCURSO >= 2088` and the raw database contents remain unchanged

#### Scenario: Import still stores full history
- **WHEN** import-history runs against the full Melate CSV while `min_contest` is configured
- **THEN** the raw database still receives contests below `min_contest` from the CSV
