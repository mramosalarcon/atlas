## ADDED Requirements

### Requirement: Fold-robust optimizer seeds from covering then polishes for fold stability
The system SHALL provide a fold-robust optimizer that constructs an initial `TicketSystem` via the covering optimizer on the provided draw set, then applies deterministic single-ticket number-replacement moves scored by a fold-robust train objective until no improving move remains within the configured pass budget.

#### Scenario: Returns a full valid system
- **WHEN** fold-robust optimize completes successfully
- **THEN** the result contains exactly `system_size` valid tickets under the provided rules

#### Scenario: Uses only provided draws
- **WHEN** fold-robust optimize runs
- **THEN** search and seeding use only the draw set passed into optimize and do not read validation or holdout draws

### Requirement: Fold-robust objective prefers worst-fold primary then sum
The system SHALL partition the provided draws into `n_folds` contiguous chronological folds using the same contiguous partition used by walk-forward evaluation, compute the primary-metric count on each fold, and score systems lexicographically by minimum fold primary, then sum of fold primaries, then aggregate primary on all provided draws, then unordered pair coverage, then triple coverage, then quad coverage.

#### Scenario: Improving worst fold is preferred
- **WHEN** a legal move increases the minimum fold primary-metric count
- **THEN** the move is accepted even if aggregate train primary is unchanged or slightly lower

#### Scenario: Sum breaks a min-fold tie
- **WHEN** two neighboring systems share the same minimum fold primary and one has a strictly greater sum of fold primaries
- **THEN** fold-robust search prefers the system with the greater sum

#### Scenario: Aggregate and coverage break remaining ties
- **WHEN** two neighboring systems tie on min-fold and sum-of-folds primary
- **THEN** search breaks ties by aggregate primary, then pairs, then triples, then quads (same coverage order as local search)

### Requirement: Fold-robust moves match local-search legality
The system SHALL only accept moves that replace exactly one main number on one ticket with a number not already on that ticket, keep tickets valid under lottery rules, and keep ticket number-sets distinct within the system.

#### Scenario: Duplicate ticket sets are rejected
- **WHEN** a candidate move would make two tickets share the same sorted number set
- **THEN** that move is skipped

### Requirement: Fold-robust search is deterministic
The system SHALL produce identical ticket systems given identical draws, rules, covering settings, fold count, and fold-robust settings.

#### Scenario: Same inputs reproduce the system
- **WHEN** fold-robust optimize is run twice with the same inputs and settings
- **THEN** both runs return identical ordered ticket number lists

### Requirement: Fold-robust output is a comparison candidate only
The system SHALL present fold-robust systems as historical search candidates for freeze-policy comparison and MUST NOT claim they predict future draws or auto-accept them.

#### Scenario: Report is non-predictive
- **WHEN** a fold-robust optimize report is produced
- **THEN** the report states the system does not predict the next draw and is not auto-accepted
