## MODIFIED Requirements

### Requirement: Apply freeze policy for accept or reject
The system SHALL accept a candidate only when the configured walk-forward fold-pass requirements are met (each passing fold having primary-metric delta ≥ `min_absolute_delta`) and, when bootstrap is enabled, the bootstrap CI lower bound is ≥ the configured `min_ci_lower`; otherwise it MUST reject the candidate. A single holdout validation window MAY be reported as a diagnostic but MUST NOT alone determine accept.

#### Scenario: Accept on walk-forward pass
- **WHEN** the number of passing folds is ≥ `required_fold_passes` and bootstrap is disabled
- **THEN** the decision is `accepted`

#### Scenario: Reject on insufficient fold passes
- **WHEN** the number of passing folds is < `required_fold_passes`
- **THEN** the decision is `rejected`

#### Scenario: Reject when bootstrap gate fails
- **WHEN** bootstrap is enabled and the CI lower bound is below `min_ci_lower`
- **THEN** the decision is `rejected`

## ADDED Requirements

### Requirement: Persist freeze-policy evidence
The system SHALL persist walk-forward fold evidence (and bootstrap summary when enabled) with each experiment, including policy version and thresholds used.

#### Scenario: Evidence retrievable after comparison
- **WHEN** a comparison completes
- **THEN** the stored experiment includes fold-level metrics and the final decision consistent with the freeze policy

#### Scenario: Rejected experiments still include evidence
- **WHEN** a candidate is rejected under the walk-forward policy
- **THEN** an experiment record is still written with decision `rejected` and fold evidence
