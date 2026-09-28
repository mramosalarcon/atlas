## Purpose

Report Atlas Confidence Intervals (ACI) as bootstrap uncertainty around historical Atlas Score and pairwise score deltas, without deciding champion promotion.

## Requirements

### Requirement: ACI provides a bootstrap confidence interval for Atlas Score
The system SHALL compute an Atlas Confidence Interval (ACI) for a system’s Atlas Score by resampling the provided draw set with replacement, recomputing the score on each resample, and reporting a percentile interval at the configured `ci_level` with a configured seed for determinism.

#### Scenario: ACI reports mean and bounds
- **WHEN** ACI is computed for a system on a non-empty draw set
- **THEN** the result includes a point score (or mean of resample scores), a lower bound, and an upper bound for the configured confidence level

#### Scenario: Same seed reproduces ACI
- **WHEN** ACI is computed twice with the same system, draws, scoring settings, resample count, ci_level, and seed
- **THEN** both runs return identical interval bounds

### Requirement: Pairwise ACI covers score deltas
The system SHALL support an ACI for the difference in Atlas Score between a baseline and a candidate on paired resamples of the same draw indices.

#### Scenario: Pairwise delta interval
- **WHEN** pairwise ACI is requested for baseline and candidate on the same draws
- **THEN** the result includes lower and upper bounds for `score(candidate) - score(baseline)`

### Requirement: ACI is diagnostic only
The system SHALL present ACI as uncertainty around historical Atlas Score and MUST NOT use ACI alone to accept or reject champion promotion (freeze policy remains authoritative).

#### Scenario: Non-promotional ACI report
- **WHEN** an ACI report is produced
- **THEN** it states the interval is historical diagnostic uncertainty and does not decide promotion
