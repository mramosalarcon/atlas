## ADDED Requirements

### Requirement: Covering optimizer settings are loaded from config
The system SHALL load covering optimizer settings from YAML config, including an enabled flag and pair-weight mode, and MUST NOT hardcode those values inside the covering strategy.

#### Scenario: Default covering settings present
- **WHEN** `config/config.yaml` defines `optimizer.covering.enabled` and `optimizer.covering.pair_weight`
- **THEN** the loaded config exposes those values to the covering optimizer

### Requirement: Missing or invalid covering settings fail clearly when covering optimize is requested
The system SHALL fail with a clear error if covering optimize is invoked while covering is disabled or `pair_weight` is not a supported mode.

#### Scenario: Covering disabled
- **WHEN** a user runs covering optimize and `optimizer.covering.enabled` is false
- **THEN** the system raises an error stating covering is disabled

#### Scenario: Unsupported pair_weight
- **WHEN** config sets an unsupported `pair_weight` value
- **THEN** configuration load or optimize setup raises an error naming the invalid value
