## ADDED Requirements

### Requirement: Shipped Melate config enables bootstrap by default
The system SHALL ship Melate configuration with freeze-policy bootstrap enabled and with documented default knobs (`n_resamples`, `ci_level`, `seed`, `min_ci_lower`) so accept decisions apply the bootstrap gate without requiring a manual config edit.

#### Scenario: Default config loads bootstrap enabled
- **WHEN** the application loads `config/config.yaml`
- **THEN** `evaluation.freeze_policy.bootstrap.enabled` is true and bootstrap numeric settings are present

### Requirement: Bootstrap numeric settings fail clearly when invalid
The system SHALL fail configuration load with a clear error when `n_resamples` is less than 1 (in addition to existing `ci_level` validation).

#### Scenario: Invalid n_resamples
- **WHEN** config sets `bootstrap.n_resamples` less than 1
- **THEN** configuration load raises an error naming `n_resamples`
