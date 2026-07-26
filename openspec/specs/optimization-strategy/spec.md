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

### Requirement: Strategies may compose other strategies for seeding
The system SHALL allow an optimization strategy to invoke another strategy solely to produce a seed system from the same provided draw set, rules, and settings, without reading validation or holdout draws.

#### Scenario: Seed composition stays on provided draws
- **WHEN** a composing strategy seeds from another strategy during optimize
- **THEN** both the seed call and the subsequent search use only the draw set passed into the outer optimize invocation

### Requirement: Strategies may run multiple seeded invocations for ensembles
The system SHALL allow an optimization strategy to invoke other strategies multiple times with different seeds on the same provided draw set for the purpose of building an ensemble ticket pool, without reading validation or holdout draws.

#### Scenario: Multi-seed composition stays on provided draws
- **WHEN** an ensemble strategy runs source strategies across multiple seeds during optimize
- **THEN** every source invocation uses only the draw set passed into the outer optimize call
