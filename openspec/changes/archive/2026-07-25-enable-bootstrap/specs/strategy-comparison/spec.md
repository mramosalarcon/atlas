## ADDED Requirements

### Requirement: Freeze policy version distinguishes bootstrap-enabled defaults
The system SHALL record a freeze-policy version string that reflects when shipped defaults include the bootstrap gate, and SHALL persist that version with experiment policy evidence.

#### Scenario: Shipped version indicates bootstrap era
- **WHEN** shipped Melate config is loaded with bootstrap enabled by default
- **THEN** `evaluation.freeze_policy.version` identifies the walk-forward-plus-bootstrap policy era

#### Scenario: Version stored on compare
- **WHEN** a comparison completes under the shipped defaults
- **THEN** the experiment policy evidence includes the same freeze-policy version string
