## ADDED Requirements

### Requirement: Local search seeds from covering then polishes tickets
The system SHALL provide a local-search optimizer that constructs an initial `TicketSystem` via the covering optimizer on the provided draw set, then applies deterministic single-ticket number-replacement moves until no improving move remains within the configured pass budget.

#### Scenario: Returns a full valid system
- **WHEN** local-search optimize completes successfully
- **THEN** the result contains exactly `system_size` valid tickets under the provided rules

#### Scenario: Seed used when no improving move exists
- **WHEN** a full neighborhood pass finds no move that improves the train objective
- **THEN** the optimizer returns the covering-seeded system (possibly unchanged)

### Requirement: Moves are valid single-number replacements
The system SHALL only accept moves that replace exactly one main number on one ticket with a number not already on that ticket, keep all tickets valid under lottery rules, and keep ticket number-sets distinct within the system.

#### Scenario: Duplicate ticket sets are rejected
- **WHEN** a candidate move would make two tickets share the same sorted number set
- **THEN** that move is skipped

### Requirement: Train objective prefers primary metric then pair coverage
The system SHALL score candidate systems on the provided draw set using the count of draws whose best ticket has at least the configured primary-metric minimum hits, and SHALL use unordered pair coverage as a tie-break when that count is equal. The strategy MUST NOT read draws outside the provided set.

#### Scenario: Improving primary metric is accepted
- **WHEN** a legal move increases the train primary-metric count
- **THEN** the move is accepted

#### Scenario: Tie uses pair coverage
- **WHEN** a legal move leaves the train primary-metric count unchanged but increases system unordered pair coverage
- **THEN** the move is accepted

### Requirement: Local search is deterministic
The system SHALL produce identical ticket systems given identical draws, rules, seed, covering settings, and local-search settings.

#### Scenario: Same inputs reproduce the system
- **WHEN** local-search optimize is run twice with the same inputs and settings
- **THEN** both runs return identical ordered ticket number lists

### Requirement: Local-search output is a comparison candidate only
The system SHALL present local-search systems as historical search candidates for freeze-policy comparison and MUST NOT claim they predict future draws or auto-accept them.

#### Scenario: Non-predictive optimize report
- **WHEN** a local-search optimize report or CLI summary is produced
- **THEN** it states the system is a candidate for historical comparison and does not predict the next draw
