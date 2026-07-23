## ADDED Requirements

### Requirement: Compute ticket hits against a draw
The system SHALL compute how many of a ticket's six main numbers match a draw's six main numbers, and SHALL expose whether the additional number matches when evaluating prize-relevant tiers that depend on it.

#### Scenario: Three main hits
- **WHEN** a ticket shares exactly three numbers with a draw's main six
- **THEN** the evaluator reports `hits=3`

#### Scenario: Perfect main match
- **WHEN** a ticket's six numbers equal the draw's six main numbers
- **THEN** the evaluator reports `hits=6`

#### Scenario: Invalid ticket rejected
- **WHEN** a ticket has the wrong count of numbers, duplicates, or numbers outside the configured range
- **THEN** evaluation raises a validation error and does not score the ticket

### Requirement: Evaluate an eight-ticket system over history
The system SHALL evaluate a system of exactly `system_size` tickets (default 8) against a provided set of draws and return aggregate metrics: counts of draws achieving at least 3, 4, 5, and 6 hits on any ticket; coverage summary; and ROI using the configured prize table and ticket cost.

#### Scenario: System size enforced
- **WHEN** a caller submits a system with a ticket count other than the configured `system_size`
- **THEN** evaluation raises a validation error

#### Scenario: Aggregate prize-tier counts
- **WHEN** a valid 8-ticket system is evaluated against a draw history
- **THEN** the result includes integer counts for draws with best-ticket hits ≥3, ≥4, ≥5, and ≥6 (or equivalent explicit 3/4/5/6 bucket counts documented in the report)

#### Scenario: Evaluation is deterministic
- **WHEN** the same system, draws, config, and prize table are evaluated twice
- **THEN** both runs produce identical metrics

### Requirement: Performance bound for full-history evaluation
The system SHALL evaluate one 8-ticket system against the full imported Melate history in under 1 second on a typical developer machine.

#### Scenario: Full history under one second
- **WHEN** a valid system is evaluated against all imported draws (~4,000+)
- **THEN** wall-clock evaluation time is less than 1.0 second (excluding import)

### Requirement: Outputs must not claim prediction
The system SHALL NOT present evaluation results as a prediction of future draw outcomes.

#### Scenario: Report language is comparative
- **WHEN** an evaluation report is generated
- **THEN** the report describes historical performance / coverage under game rules and does not claim knowledge of the next draw
