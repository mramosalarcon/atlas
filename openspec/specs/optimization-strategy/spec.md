## Purpose

Define a common optimizer interface that produces valid ticket systems from a caller-provided draw set (train window only).

## Requirements

### Requirement: Optimizers implement a common strategy interface
The system SHALL expose an optimization strategy interface that accepts a draw set, lottery rules, and optimizer settings, and returns a valid `TicketSystem` of configured `system_size` without mutating the raw history database.

#### Scenario: Interface returns a full valid system
- **WHEN** any registered strategy's optimize method completes successfully
- **THEN** the result contains exactly `system_size` valid tickets under the provided rules

### Requirement: Optimization search uses only the provided draw set
The system SHALL run optimizer search exclusively on the draw set passed into the strategy (callers MUST pass the train window) and MUST NOT read validation draws inside the strategy implementation.

#### Scenario: Strategy does not require validation draws
- **WHEN** optimize is invoked with only train draws
- **THEN** the strategy produces a system without accessing other draw partitions
