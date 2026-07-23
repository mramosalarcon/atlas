## ADDED Requirements

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
