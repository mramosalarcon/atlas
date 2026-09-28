## ADDED Requirements

### Requirement: Walk-forward folds run on the filtered contest sequence
When `evaluation.min_contest` is set, the system SHALL build walk-forward folds from the ascending filtered contest sequence only (contests `>= min_contest`).

#### Scenario: Early contests excluded from folds
- **WHEN** freeze-policy comparison runs with `min_contest=2088`
- **THEN** no fold contest range includes a contest id less than 2088
