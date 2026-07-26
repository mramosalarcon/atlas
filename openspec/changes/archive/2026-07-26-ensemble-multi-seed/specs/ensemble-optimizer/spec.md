## ADDED Requirements

### Requirement: Ensemble pools unique tickets from multi-seed strategy runs
The system SHALL provide an ensemble optimizer that, for each configured seed and each configured source strategy, runs that strategy on the provided draw set and pools unique tickets by sorted number tuple.

#### Scenario: Multiple seeds contribute tickets
- **WHEN** ensemble optimize runs with at least two seeds and at least one source strategy
- **THEN** the ticket pool contains the union of unique tickets produced across those runs

#### Scenario: Duplicate tickets are stored once
- **WHEN** two runs produce the same sorted ticket numbers
- **THEN** the pool retains a single copy of that ticket

### Requirement: Ensemble drafts a full system from the pool
The system SHALL draft exactly `system_size` distinct tickets from the pool by repeatedly selecting the unused ticket that maximizes the train objective on the provided draw set (primary-metric count, then unordered pair coverage), with deterministic tie-breaks.

#### Scenario: Draft size matches system_size
- **WHEN** the pool contains at least `system_size` unique tickets
- **THEN** ensemble optimize returns a valid `TicketSystem` with exactly `system_size` tickets

#### Scenario: Insufficient pool fails clearly
- **WHEN** the pool has fewer than `system_size` unique tickets
- **THEN** the system raises an error stating the pool is too small

### Requirement: Ensemble may draft from exported system files
The system SHALL allow building the ticket pool from one or more existing system JSON files (in addition to or instead of generate mode) without reading validation draws.

#### Scenario: File sources contribute to the pool
- **WHEN** ensemble is invoked with system JSON source paths
- **THEN** tickets from those files are included in the pool before drafting

### Requirement: Ensemble search stays on the provided draw set
The system SHALL run all source strategies and the draft scoring exclusively on the draw set passed into optimize (train window) and MUST NOT read holdout or validation partitions inside the ensemble implementation.

#### Scenario: Train-only contract
- **WHEN** ensemble optimize is invoked with only train draws
- **THEN** it produces a system without accessing other draw partitions

### Requirement: Ensemble output is a comparison candidate only
The system SHALL present ensemble systems as historical search candidates for freeze-policy comparison and MUST NOT claim they predict future draws or auto-accept them.

#### Scenario: Non-predictive optimize report
- **WHEN** an ensemble optimize report or CLI summary is produced
- **THEN** it states the system is a candidate for historical comparison and does not predict the next draw
