## ADDED Requirements

### Requirement: Greedy builds an eight-ticket system by incremental pair coverage
The system SHALL provide a greedy optimizer that constructs tickets one at a time, selecting at each step a candidate ticket that maximizes the number of new unordered main-number pairs covered relative to tickets already chosen, until `system_size` tickets are produced.

#### Scenario: First ticket maximizes pair count among candidates
- **WHEN** the greedy optimizer starts with an empty system and a non-empty candidate pool
- **THEN** the first selected ticket is one with the maximum number of distinct unordered pairs among candidates (ties broken deterministically)

#### Scenario: Later tickets prefer new pairs
- **WHEN** at least one ticket is already selected
- **THEN** the next ticket chosen maximizes newly covered pairs not already present in the selected set's pair union

### Requirement: Greedy search is deterministic for a fixed seed
The system SHALL generate candidate tickets using a configured seed such that identical inputs (draws, rules, seed, pool size) produce the identical ticket system.

#### Scenario: Same seed reproduces the system
- **WHEN** greedy optimize is run twice with the same seed, rules, draw set, and candidate pool size
- **THEN** both runs return ticket systems with identical number lists in order

### Requirement: Greedy output is a comparison candidate only
The system SHALL present greedy-optimized systems as historical search candidates for evaluation/comparison and MUST NOT claim they predict future draws or auto-accept them without the freeze policy.

#### Scenario: Non-predictive optimize report
- **WHEN** a greedy optimize report or CLI summary is produced
- **THEN** it states the system is a candidate for historical comparison and does not predict the next draw
