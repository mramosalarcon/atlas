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

### Requirement: Optional tournament defaults are loaded from config
The system SHALL load optional tournament defaults from YAML when a `tournament` section is present, including a default champion path and roster glob, and MUST NOT require that section for other ATLAS commands to work.

#### Scenario: Tournament section absent is allowed
- **WHEN** config has no `tournament` section
- **THEN** configuration load succeeds and tournament CLI requires explicit champion/challenger arguments

#### Scenario: Defaults exposed when present
- **WHEN** `config/config.yaml` defines `tournament.champion` and `tournament.roster_glob`
- **THEN** the loaded config exposes those values for tournament CLI defaults

### Requirement: Freeze-policy settings are loaded from config
The system SHALL load freeze-policy settings from YAML config, including walk-forward fold count, required fold passes, and optional bootstrap parameters, and MUST NOT hardcode those values inside the comparison engine.

#### Scenario: Default walk-forward settings present
- **WHEN** config defines `n_folds` and `required_fold_passes` under the freeze-policy section
- **THEN** the loaded config exposes those values to strategy comparison

#### Scenario: Bootstrap settings optional with defaults
- **WHEN** bootstrap is present with `enabled`, `n_resamples`, `ci_level`, `seed`, and `min_ci_lower`
- **THEN** the loaded config exposes those bootstrap settings to comparison

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

### Requirement: Invalid freeze-policy config fails clearly
The system SHALL fail with a clear error if freeze-policy settings are inconsistent (e.g. `required_fold_passes` greater than `n_folds`, or `n_folds` < 2).

#### Scenario: required passes exceed folds
- **WHEN** config sets `required_fold_passes` greater than `n_folds`
- **THEN** configuration load or comparison setup raises an error naming the inconsistency
