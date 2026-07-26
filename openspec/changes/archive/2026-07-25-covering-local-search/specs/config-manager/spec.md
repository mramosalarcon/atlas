## ADDED Requirements

### Requirement: Local-search optimizer settings are loaded from config
The system SHALL load local-search optimizer settings from YAML config, including an enabled flag and a maximum pass budget, and MUST NOT hardcode those values inside the local-search strategy.

#### Scenario: Default local-search settings present
- **WHEN** `config/config.yaml` defines `optimizer.local_search.enabled` and `optimizer.local_search.max_passes`
- **THEN** the loaded config exposes those values to the local-search optimizer

### Requirement: Missing or invalid local-search settings fail clearly when local optimize is requested
The system SHALL fail with a clear error if local-search optimize is invoked while local search is disabled, or if `max_passes` is less than 1.

#### Scenario: Local search disabled
- **WHEN** a user runs local-search optimize and `optimizer.local_search.enabled` is false
- **THEN** the system raises an error stating local search is disabled

#### Scenario: Invalid max_passes
- **WHEN** config sets `max_passes` less than 1
- **THEN** configuration load or optimize setup raises an error naming the invalid value
