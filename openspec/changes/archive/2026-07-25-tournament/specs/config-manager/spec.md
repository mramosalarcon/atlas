## ADDED Requirements

### Requirement: Optional tournament defaults are loaded from config
The system SHALL load optional tournament defaults from YAML when a `tournament` section is present, including a default champion path and roster glob, and MUST NOT require that section for other ATLAS commands to work.

#### Scenario: Tournament section absent is allowed
- **WHEN** config has no `tournament` section
- **THEN** configuration load succeeds and tournament CLI requires explicit champion/challenger arguments

#### Scenario: Defaults exposed when present
- **WHEN** `config/config.yaml` defines `tournament.champion` and `tournament.roster_glob`
- **THEN** the loaded config exposes those values for tournament CLI defaults
