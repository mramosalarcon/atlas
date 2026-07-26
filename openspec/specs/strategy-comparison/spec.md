## Purpose

Compare baseline and candidate 8-ticket systems under a walk-forward freeze policy (with optional bootstrap), report holdout diagnostics, and persist experiment decisions with policy evidence.

## Requirements

### Requirement: Compare baseline and candidate on validation window
The system SHALL compute holdout diagnostic metrics for baseline and candidate on the configured chronological validation window and label the window (contest range), while freeze accept/reject is determined by walk-forward policy rather than this window alone.

#### Scenario: Metrics computed on validation only
- **WHEN** a comparison is requested with a chronological validation split
- **THEN** both systems are scored on the same validation draws and the comparison result labels the window (e.g. contest range)

#### Scenario: Clear better/worse/tie outcome
- **WHEN** comparison finishes
- **THEN** the result states whether the candidate improved, tied, or worsened on the primary metric relative to the baseline on the holdout diagnostic window

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

### Requirement: Persist experiment records
The system SHALL append an experiment record for every comparison including: timestamp, baseline and candidate identifiers or ticket sets, validation window, primary metric values, delta, decision (`accepted`/`rejected`), and config threshold used.

#### Scenario: Experiment is retrievable after comparison
- **WHEN** a comparison completes
- **THEN** a durable experiment record exists that can be listed later and matches the decision returned to the caller

#### Scenario: Rejected experiments are still logged
- **WHEN** a candidate is rejected
- **THEN** an experiment record is still written with decision `rejected`

### Requirement: Persist freeze-policy evidence
The system SHALL persist walk-forward fold evidence (and bootstrap summary when enabled) with each experiment, including policy version and thresholds used.

#### Scenario: Evidence retrievable after comparison
- **WHEN** a comparison completes
- **THEN** the stored experiment includes fold-level metrics and the final decision consistent with the freeze policy

#### Scenario: Rejected experiments still include evidence
- **WHEN** a candidate is rejected under the walk-forward policy
- **THEN** an experiment record is still written with decision `rejected` and fold evidence

### Requirement: Freeze policy version distinguishes bootstrap-enabled defaults
The system SHALL record a freeze-policy version string that reflects when shipped defaults include the bootstrap gate, and SHALL persist that version with experiment policy evidence.

#### Scenario: Shipped version indicates bootstrap era
- **WHEN** shipped Melate config is loaded with bootstrap enabled by default
- **THEN** `evaluation.freeze_policy.version` identifies the walk-forward-plus-bootstrap policy era

#### Scenario: Version stored on compare
- **WHEN** a comparison completes under the shipped defaults
- **THEN** the experiment policy evidence includes the same freeze-policy version string
