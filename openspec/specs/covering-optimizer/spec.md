## Purpose

Construct an 8-ticket Melate system via covering-design growth over priority uncovered pairs for freeze-policy comparison.

## Requirements

### Requirement: Covering optimizer builds tickets from priority pairs
The system SHALL provide a covering-design optimizer that constructs `system_size` tickets by repeatedly selecting numbers to cover high-priority still-uncovered unordered pairs until each ticket has `main_count` numbers.

#### Scenario: Empty ticket seeds from top uncovered pair
- **WHEN** a new ticket is empty and uncovered priority pairs remain
- **THEN** the optimizer seeds the ticket with the two numbers of the highest-priority uncovered pair (ties broken deterministically)

#### Scenario: Subsequent numbers extend pair coverage
- **WHEN** a ticket already contains at least one number and needs more numbers
- **THEN** the next number chosen maximizes the priority sum of uncovered pairs linking it to numbers already on the ticket (ties broken deterministically)

### Requirement: Pair priority modes are configurable
The system SHALL support at least `train_frequency` (weight pairs by co-appearance in the provided draw set) and `uniform` (equal weight, lex order) priority modes.

#### Scenario: Train frequency prefers common pairs
- **WHEN** `pair_weight=train_frequency` and pair `{1,2}` appears more often than `{3,4}` in the provided draws
- **THEN** `{1,2}` is ordered strictly before `{3,4}` in the priority list (absent other ties)

#### Scenario: Uniform mode is lex-stable
- **WHEN** `pair_weight=uniform`
- **THEN** pair priority order is deterministic lexicographic order over valid pairs in range

### Requirement: Covering search is deterministic
The system SHALL produce identical ticket systems given identical draws, rules, seed, and covering settings.

#### Scenario: Same inputs reproduce the system
- **WHEN** covering optimize is run twice with the same inputs and settings
- **THEN** both runs return identical ordered ticket number lists

### Requirement: Covering output is a comparison candidate only
The system SHALL present covering-optimized systems as historical search candidates for freeze-policy comparison and MUST NOT claim they predict future draws or auto-accept them.

#### Scenario: Non-predictive optimize report
- **WHEN** a covering optimize report or CLI summary is produced
- **THEN** it states the system is a candidate for historical comparison and does not predict the next draw
