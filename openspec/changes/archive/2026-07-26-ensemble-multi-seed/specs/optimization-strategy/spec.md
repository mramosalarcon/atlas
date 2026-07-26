## ADDED Requirements

### Requirement: Strategies may run multiple seeded invocations for ensembles
The system SHALL allow an optimization strategy to invoke other strategies multiple times with different seeds on the same provided draw set for the purpose of building an ensemble ticket pool, without reading validation or holdout draws.

#### Scenario: Multi-seed composition stays on provided draws
- **WHEN** an ensemble strategy runs source strategies across multiple seeds during optimize
- **THEN** every source invocation uses only the draw set passed into the outer optimize call
