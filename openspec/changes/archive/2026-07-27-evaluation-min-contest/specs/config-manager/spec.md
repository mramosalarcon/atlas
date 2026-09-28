## ADDED Requirements

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
