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

### Requirement: Covering cover orders and order weights are loaded from config
The system SHALL load covering `cover_orders` and per-order relative weights from YAML config and expose them to the covering optimizer, and MUST NOT hardcode those values inside the covering strategy.

#### Scenario: Default cover orders and weights present
- **WHEN** `config/config.yaml` defines `optimizer.covering.cover_orders` and `optimizer.covering.order_weights`
- **THEN** the loaded config exposes those values to the covering optimizer

### Requirement: Invalid covering multi-order settings fail clearly
The system SHALL fail configuration load with a clear error if `cover_orders` is empty, contains a value outside `{2, 3, 4}`, omits `2`, or if `order_weights` is missing a required order or has a non-positive weight.

#### Scenario: Cover orders omit pairs
- **WHEN** config sets `cover_orders` without `2`
- **THEN** configuration load raises an error stating order 2 is required

#### Scenario: Unsupported cover order
- **WHEN** config lists a cover order other than 2, 3, or 4
- **THEN** configuration load raises an error naming the invalid order

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

### Requirement: Scoring settings are loaded from config
The system SHALL load Atlas Score weights, Elo settings (initial rating, K-factor, ratings store path), and ACI settings (n_resamples, ci_level, seed) from YAML config and MUST NOT hardcode those values inside scoring implementations.

#### Scenario: Default scoring section present
- **WHEN** `config/config.yaml` defines a `scoring` section with weights, elo, and aci subsections
- **THEN** the loaded config exposes those values to scoring, rating, and ACI components

### Requirement: Invalid scoring settings fail clearly
The system SHALL fail configuration load with a clear error if Elo `k_factor` is not positive, if ACI `n_resamples` is less than 1, or if `ci_level` is not in `(0, 1)`.

#### Scenario: Invalid ACI n_resamples
- **WHEN** config sets `scoring.aci.n_resamples` less than 1
- **THEN** configuration load raises an error naming `n_resamples`

#### Scenario: Invalid Elo k_factor
- **WHEN** config sets `scoring.elo.k_factor` less than or equal to 0
- **THEN** configuration load raises an error naming `k_factor`

### Requirement: Optional minimum contest floor is loaded from config
The system SHALL load an optional `evaluation.min_contest` integer from YAML config and expose it to evaluation draw loading, and MUST NOT hardcode a Melate contest floor inside domain logic.

#### Scenario: Default Melate config sets min_contest 2088
- **WHEN** the application loads shipped `config/config.yaml`
- **THEN** `evaluation.min_contest` is 2088

#### Scenario: Absent min_contest means no floor
- **WHEN** config omits `evaluation.min_contest` or sets it to null
- **THEN** evaluation draw loading uses all imported contests

### Requirement: Invalid min_contest fails clearly
The system SHALL fail configuration load with a clear error if `min_contest` is present and less than 1.

#### Scenario: Non-positive min_contest
- **WHEN** config sets `evaluation.min_contest` to 0 or a negative value
- **THEN** configuration load raises an error naming `min_contest`

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

### Requirement: Fold-robust seed_from path is loaded from config
The system SHALL load an optional `optimizer.fold_robust.seed_from` path from YAML config (null or omitted means covering seed) and expose it to the fold-robust optimizer.

#### Scenario: Default Melate config seeds from champion export
- **WHEN** the application loads shipped `config/config.yaml` after this change
- **THEN** `optimizer.fold_robust.seed_from` resolves to the local-search champion export path used as the tournament champion

#### Scenario: Null seed_from means covering
- **WHEN** config sets `optimizer.fold_robust.seed_from` to null or omits it
- **THEN** fold-robust uses covering seed unless the CLI overrides the path

### Requirement: Fold-robust objective mode is loaded from config
The system SHALL load `optimizer.fold_robust.objective` as `absolute` or `relative` (default `absolute` when omitted) and an optional `optimizer.fold_robust.relative_to` path (null/omit means fall back to seed_from then tournament.champion at optimize time).

#### Scenario: Default objective is absolute
- **WHEN** the application loads config that omits `optimizer.fold_robust.objective`
- **THEN** fold-robust objective resolves to `absolute`

#### Scenario: Relative mode and relative_to are exposed
- **WHEN** config sets `optimizer.fold_robust.objective` to `relative` and optionally `relative_to` to a path
- **THEN** those settings are available to the fold-robust optimizer

### Requirement: Invalid fold-robust objective fails clearly
The system SHALL fail configuration load with a clear error if `optimizer.fold_robust.objective` is not `absolute` or `relative`.

#### Scenario: Unknown objective value
- **WHEN** config sets `optimizer.fold_robust.objective` to a value other than `absolute` or `relative`
- **THEN** configuration load raises an error naming `objective`
