## ADDED Requirements

### Requirement: Optimizer settings are loaded from config
The system SHALL load optimizer settings from YAML config, including at least a seed and candidate pool size for greedy search, and MUST NOT hardcode those values inside the optimizer implementation.

#### Scenario: Default optimizer seed and pool size
- **WHEN** `config/config.yaml` defines optimizer `seed` and `candidate_pool_size`
- **THEN** the loaded config exposes those values to the greedy optimizer

### Requirement: Missing optimizer config fails clearly when optimize is requested
The system SHALL fail with a clear error if an optimize command is invoked but required optimizer settings are absent from config.

#### Scenario: Optimizer section missing
- **WHEN** a user runs greedy optimize against a config without an `optimizer` section
- **THEN** the system raises an error naming the missing optimizer configuration
