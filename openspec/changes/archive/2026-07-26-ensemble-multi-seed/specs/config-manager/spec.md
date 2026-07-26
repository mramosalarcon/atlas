## ADDED Requirements

### Requirement: Ensemble optimizer settings are loaded from config
The system SHALL load ensemble optimizer settings from YAML config, including an enabled flag, a list of seeds, and a list of source strategy names, and MUST NOT hardcode those values inside the ensemble strategy.

#### Scenario: Default ensemble settings present
- **WHEN** `config/config.yaml` defines `optimizer.ensemble.enabled`, `optimizer.ensemble.seeds`, and `optimizer.ensemble.sources`
- **THEN** the loaded config exposes those values to the ensemble optimizer

### Requirement: Invalid ensemble settings fail clearly
The system SHALL fail with a clear error if ensemble optimize is invoked while ensemble is disabled, if `seeds` is empty, if `sources` is empty, or if a source name is not supported.

#### Scenario: Ensemble disabled
- **WHEN** a user runs ensemble optimize and `optimizer.ensemble.enabled` is false
- **THEN** the system raises an error stating ensemble is disabled

#### Scenario: Unsupported source strategy
- **WHEN** config lists a source strategy name that is not supported
- **THEN** configuration load or optimize setup raises an error naming the invalid source
