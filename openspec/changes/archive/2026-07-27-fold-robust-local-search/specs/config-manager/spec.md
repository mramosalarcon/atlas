## ADDED Requirements

### Requirement: Fold-robust optimizer settings are loaded from config
The system SHALL load `optimizer.fold_robust` settings including `enabled`, `max_passes`, and `primary_metric_min_hits` from YAML config and expose them to the fold-robust optimizer.

#### Scenario: Default Melate config enables fold-robust
- **WHEN** the application loads shipped `config/config.yaml` after this change
- **THEN** `optimizer.fold_robust.enabled` is true and `max_passes` and `primary_metric_min_hits` are present

### Requirement: Invalid fold-robust settings fail clearly
The system SHALL fail configuration load with a clear error if `fold_robust.max_passes` is less than 1.

#### Scenario: Non-positive max_passes
- **WHEN** config sets `optimizer.fold_robust.max_passes` to 0 or a negative value
- **THEN** configuration load raises an error naming `max_passes`
