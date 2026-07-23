## Purpose

Compare baseline and candidate 8-ticket systems on a held-out validation window, apply the freeze policy, and persist experiment decisions.

## Requirements

### Requirement: Compare baseline and candidate on validation window
The system SHALL compare a baseline 8-ticket system against a candidate 8-ticket system using only the configured validation window of draws (held out from design/training use in this workflow).

#### Scenario: Metrics computed on validation only
- **WHEN** a comparison is requested with a chronological validation split
- **THEN** both systems are scored on the same validation draws and the comparison result labels the window (e.g. contest range)

#### Scenario: Clear better/worse/tie outcome
- **WHEN** comparison finishes
- **THEN** the result states whether the candidate improved, tied, or worsened on the primary metric relative to the baseline

### Requirement: Apply freeze policy for accept or reject
The system SHALL accept a candidate only when its primary metric on the validation window is strictly greater than the baseline by at least the configured `min_absolute_delta`; otherwise it MUST reject the candidate.

#### Scenario: Accept on sufficient improvement
- **WHEN** the candidate's primary metric exceeds the baseline by ≥ `min_absolute_delta` on validation
- **THEN** the decision is `accepted`

#### Scenario: Reject on insufficient improvement
- **WHEN** the candidate does not exceed the baseline by `min_absolute_delta` on validation
- **THEN** the decision is `rejected`

### Requirement: Persist experiment records
The system SHALL append an experiment record for every comparison including: timestamp, baseline and candidate identifiers or ticket sets, validation window, primary metric values, delta, decision (`accepted`/`rejected`), and config threshold used.

#### Scenario: Experiment is retrievable after comparison
- **WHEN** a comparison completes
- **THEN** a durable experiment record exists that can be listed later and matches the decision returned to the caller

#### Scenario: Rejected experiments are still logged
- **WHEN** a candidate is rejected
- **THEN** an experiment record is still written with decision `rejected`
