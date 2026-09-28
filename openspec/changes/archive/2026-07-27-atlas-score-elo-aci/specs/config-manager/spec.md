## ADDED Requirements

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
