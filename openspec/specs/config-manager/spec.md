## Purpose

Load Melate lottery rules and evaluation settings from external YAML configuration so domain logic stays game-agnostic.

## Requirements

### Requirement: External configuration loads Melate rules
The system SHALL load lottery rules and evaluation settings from a YAML config file and MUST NOT hardcode Melate pool size, number range, main-number count, or system size inside domain logic.

#### Scenario: Load default Melate config
- **WHEN** the application starts with `config/config.yaml` present
- **THEN** it exposes rules with `min_number=1`, `max_number=56`, `main_count=6`, and `system_size=8`

#### Scenario: Missing config fails clearly
- **WHEN** the configured config path does not exist
- **THEN** the system raises an error that names the missing path and does not proceed with defaults silently

### Requirement: Validation and evaluation windows are configurable
The system SHALL read train/validation split ratios (or absolute concurso cutoffs) and accept/reject thresholds from config.

#### Scenario: Default chronological split
- **WHEN** config specifies `validation_ratio=0.15` and no absolute cutoffs
- **THEN** the newest 15% of draws by ascending `CONCURSO` form the validation window and the remainder form the train window

#### Scenario: Accept threshold is versioned
- **WHEN** an experiment is recorded
- **THEN** the stored record includes the `min_absolute_delta` (or equivalent threshold) that was active from config

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
