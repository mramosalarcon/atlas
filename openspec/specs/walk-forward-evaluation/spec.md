## Purpose

Partition Melate history into contiguous chronological folds and score baseline vs candidate per fold for freeze-policy decisions.

## Requirements

### Requirement: Chronological walk-forward folds
The system SHALL partition contest-ordered draws into a configured number of contiguous folds and evaluate baseline and candidate primary metrics independently on each fold's test segment.

#### Scenario: Equal fold partition
- **WHEN** `n_folds=5` and at least 5 draws exist
- **THEN** the system produces 5 non-empty contiguous test segments covering all draws in contest order without overlap

#### Scenario: Fold metrics recorded
- **WHEN** walk-forward evaluation completes
- **THEN** each fold record includes fold index, contest range, baseline metric, candidate metric, and delta

### Requirement: Fold pass uses absolute delta floor
The system SHALL mark a fold as passed only when the candidate primary metric exceeds the baseline by at least `min_absolute_delta` on that fold's test segment.

#### Scenario: Fold passes on sufficient delta
- **WHEN** a fold delta is ≥ `min_absolute_delta`
- **THEN** that fold is marked passed

#### Scenario: Fold fails on insufficient delta
- **WHEN** a fold delta is < `min_absolute_delta`
- **THEN** that fold is marked failed

### Requirement: Walk-forward folds run on the filtered contest sequence
When `evaluation.min_contest` is set, the system SHALL build walk-forward folds from the ascending filtered contest sequence only (contests `>= min_contest`).

#### Scenario: Early contests excluded from folds
- **WHEN** freeze-policy comparison runs with `min_contest=2088`
- **THEN** no fold contest range includes a contest id less than 2088
