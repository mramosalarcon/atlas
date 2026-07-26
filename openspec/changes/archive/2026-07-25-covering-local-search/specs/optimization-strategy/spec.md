## ADDED Requirements

### Requirement: Strategies may compose other strategies for seeding
The system SHALL allow an optimization strategy to invoke another strategy solely to produce a seed system from the same provided draw set, rules, and settings, without reading validation or holdout draws.

#### Scenario: Seed composition stays on provided draws
- **WHEN** a composing strategy seeds from another strategy during optimize
- **THEN** both the seed call and the subsequent search use only the draw set passed into the outer optimize invocation
