## ADDED Requirements

### Requirement: Fold-robust is a registered optimization strategy
The system SHALL expose fold-robust optimization through the common optimization strategy interface used by other Melate system optimizers.

#### Scenario: Strategy returns a valid system from train draws
- **WHEN** the fold-robust strategy optimize method completes successfully on a train draw set
- **THEN** the result contains exactly `system_size` valid tickets and search used only that draw set
