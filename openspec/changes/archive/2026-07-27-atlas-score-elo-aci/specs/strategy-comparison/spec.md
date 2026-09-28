## ADDED Requirements

### Requirement: Comparison reports may include Atlas Score and ACI diagnostics
The system SHALL allow comparison reports to include Atlas Score (and optional ACI) for baseline and candidate on a documented draw window as diagnostics, and MUST NOT change the freeze-policy accept/reject decision based on those diagnostics.

#### Scenario: Diagnostics do not flip decision
- **WHEN** comparison includes Atlas Score or ACI diagnostics and freeze policy would reject
- **THEN** the recorded decision remains `rejected` regardless of score ordering

#### Scenario: Diagnostic banner remains non-predictive
- **WHEN** comparison output includes Atlas Score or ACI lines
- **THEN** the overall comparison report still states it is not a prediction of future draws
