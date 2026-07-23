## ADDED Requirements

### Requirement: Freeze-policy settings are loaded from config
The system SHALL load freeze-policy settings from YAML config, including walk-forward fold count, required fold passes, and optional bootstrap parameters, and MUST NOT hardcode those values inside the comparison engine.

#### Scenario: Default walk-forward settings present
- **WHEN** config defines `n_folds` and `required_fold_passes` under the freeze-policy section
- **THEN** the loaded config exposes those values to strategy comparison

#### Scenario: Bootstrap settings optional with defaults
- **WHEN** bootstrap is present with `enabled`, `n_resamples`, `ci_level`, `seed`, and `min_ci_lower`
- **THEN** the loaded config exposes those bootstrap settings to comparison

### Requirement: Invalid freeze-policy config fails clearly
The system SHALL fail with a clear error if freeze-policy settings are inconsistent (e.g. `required_fold_passes` greater than `n_folds`, or `n_folds` < 2).

#### Scenario: required passes exceed folds
- **WHEN** config sets `required_fold_passes` greater than `n_folds`
- **THEN** configuration load or comparison setup raises an error naming the inconsistency
