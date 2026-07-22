## ADDED Requirements

### Requirement: Import Melate CSV into immutable raw storage
The system SHALL read `data/raw/Melate.csv` (or a configured path), parse each row into a draw, and persist draws into a SQLite raw database without modifying the source CSV.

#### Scenario: Successful import of valid history
- **WHEN** a valid Melate CSV with columns including `CONCURSO`, `R1`–`R6`, `R7`, `FECHA` is imported
- **THEN** every row is stored as a draw with six main numbers, one additional number, contest id, and date, and the raw CSV file remains unchanged

#### Scenario: Rebuild replaces prior raw DB contents
- **WHEN** import is run again against an existing raw database
- **THEN** the database contains exactly the draws from the latest successful import (no duplicated contests)

### Requirement: Reject invalid draws
The system SHALL reject draws that violate configured lottery rules and MUST fail the import (or report a fatal validation error) when any invalid row is present, rather than silently skipping.

#### Scenario: Number out of range
- **WHEN** a row contains a main or additional number outside the configured min/max inclusive range
- **THEN** import fails with an error identifying the contest id and the invalid number

#### Scenario: Duplicate numbers in a draw
- **WHEN** a row has repeated numbers among the six main numbers
- **THEN** import fails with an error identifying the contest id

#### Scenario: Main numbers not sorted ascending
- **WHEN** a row's main numbers are not in ascending order
- **THEN** import fails with an error identifying the contest id

### Requirement: Contest integrity checks
The system SHALL verify that contest identifiers are unique and that, after sorting by `CONCURSO`, identifiers form a contiguous sequence with no gaps for the imported set (or report the first gap).

#### Scenario: Duplicate contest id
- **WHEN** two rows share the same `CONCURSO`
- **THEN** import fails with an error identifying the duplicated contest id

#### Scenario: Gap in contest sequence
- **WHEN** sorted contest ids skip a value between the minimum and maximum imported contest
- **THEN** import fails with an error identifying the missing contest id
