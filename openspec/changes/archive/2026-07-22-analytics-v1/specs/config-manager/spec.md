## ADDED Requirements

### Requirement: Analytics settings are loaded from config
The system SHALL load analytics settings from the YAML config, including rolling window sizes and the analytics database (or export) path, and MUST NOT hardcode those window sizes in analytics business logic.

#### Scenario: Default rolling windows present
- **WHEN** `config/config.yaml` includes analytics rolling windows `[10, 20, 50, 100]`
- **THEN** the loaded config exposes exactly those window sizes to analytics components

#### Scenario: Analytics path is configurable
- **WHEN** config sets an analytics database path under `data/processed/`
- **THEN** analytics persistence uses that path rather than a hardcoded location

### Requirement: Missing analytics config fails clearly when analytics are requested
The system SHALL fail with a clear error if analytics features are invoked but required analytics settings are absent from config.

#### Scenario: Analytics section missing
- **WHEN** a user runs an analytics build command against a config without an `analytics` section
- **THEN** the system raises an error naming the missing analytics configuration
