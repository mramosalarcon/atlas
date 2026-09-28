## ADDED Requirements

### Requirement: Fold-robust may seed from a ticket-system file
The system SHALL allow fold-robust optimize to load an initial `TicketSystem` from a configured or CLI-provided JSON path under lottery rules, and SHALL fall back to the covering optimizer seed when no seed path is provided.

#### Scenario: File seed used when configured
- **WHEN** fold-robust optimize runs with a valid `seed_from` path to an 8-ticket system JSON
- **THEN** hill climb starts from that system rather than a covering-built seed

#### Scenario: Covering seed when path omitted
- **WHEN** fold-robust optimize runs with no seed path configured and no CLI override
- **THEN** the initial system is produced by the covering optimizer on the provided train draws

#### Scenario: Missing seed file fails clearly
- **WHEN** fold-robust optimize is asked to seed from a path that does not exist
- **THEN** the command fails with an error naming the missing path and does not export a candidate

### Requirement: Fold-robust report names the seed source
The system SHALL include the seed source in the fold-robust optimize report (`covering` or the seed file path) while remaining a non-predictive comparison candidate.

#### Scenario: Report shows file seed
- **WHEN** a fold-robust report is produced after seeding from a JSON file
- **THEN** the report identifies that file path as the seed source

## MODIFIED Requirements

### Requirement: Fold-robust optimizer seeds from covering then polishes for fold stability
The system SHALL provide a fold-robust optimizer that constructs an initial `TicketSystem` either via the covering optimizer on the provided draw set or via an optional seed ticket-system file, then applies deterministic single-ticket number-replacement moves scored by a fold-robust train objective until no improving move remains within the configured pass budget.

#### Scenario: Returns a full valid system
- **WHEN** fold-robust optimize completes successfully
- **THEN** the result contains exactly `system_size` valid tickets under the provided rules

#### Scenario: Uses only provided draws
- **WHEN** fold-robust optimize runs
- **THEN** search uses only the draw set passed into optimize and does not read validation or holdout draws (file seeding loads tickets only, not extra history)

#### Scenario: Same inputs reproduce the system for a given seed mode
- **WHEN** fold-robust optimize is run twice with the same draws, rules, settings, fold count, and seed path (or covering mode)
- **THEN** both runs return identical ordered ticket number lists
