## ADDED Requirements

### Requirement: Fold-robust seed_from path is loaded from config
The system SHALL load an optional `optimizer.fold_robust.seed_from` path from YAML config (null or omitted means covering seed) and expose it to the fold-robust optimizer.

#### Scenario: Default Melate config seeds from champion export
- **WHEN** the application loads shipped `config/config.yaml` after this change
- **THEN** `optimizer.fold_robust.seed_from` resolves to the local-search champion export path used as the tournament champion

#### Scenario: Null seed_from means covering
- **WHEN** config sets `optimizer.fold_robust.seed_from` to null or omits it
- **THEN** fold-robust uses covering seed unless the CLI overrides the path
