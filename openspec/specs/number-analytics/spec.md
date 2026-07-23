## Purpose

Compute per-number historical appearance profiles (frequency, rolling windows, recency, additional counts) as diagnostics over Melate history.

## Requirements

### Requirement: Per-number historical profiles
The system SHALL compute, for each number in the configured lottery range, a profile over a specified draw set including: total main-number appearance count, rolling appearance counts for each configured window size, contests since last main appearance (recency), and count of appearances as the additional number.

#### Scenario: Profile covers full number range
- **WHEN** analytics are built for Melate rules with `min_number=1` and `max_number=56`
- **THEN** the result includes exactly one profile entry for each integer from 1 through 56

#### Scenario: Rolling window uses newest draws
- **WHEN** a rolling window size of 10 is configured and at least 10 draws exist
- **THEN** each number's window-10 count equals its main appearances in the 10 highest-`CONCURSO` draws of the selected set

#### Scenario: Recency for numbers that never appeared
- **WHEN** a number has zero main appearances in the selected draw set
- **THEN** its recency value is reported as null/absent (not zero)

### Requirement: Number analytics are deterministic diagnostics
The system SHALL produce identical number profiles given the same draws, rules, and window configuration, and MUST present them as historical diagnostics rather than predictions of future draws.

#### Scenario: Deterministic rebuild
- **WHEN** number profiles are computed twice on the same inputs
- **THEN** both results are equal field-for-field

#### Scenario: Non-predictive report language
- **WHEN** a number profile report is generated
- **THEN** the report states that values describe historical appearance patterns and do not predict the next draw
