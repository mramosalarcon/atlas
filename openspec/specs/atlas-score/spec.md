## Purpose

Compute a deterministic composite Atlas Score for an 8-ticket system on a caller-provided historical draw set as a diagnostic ranking signal (not a prediction or promotion decision).

## Requirements

### Requirement: Atlas Score is a deterministic composite of historical components
The system SHALL compute an Atlas Score for a ticket system on a caller-provided draw set as a weighted sum of configured components (at least primary-metric count and unordered pair coverage), and MUST produce identical scores given identical system, draws, rules, and scoring weights.

#### Scenario: Same inputs reproduce the score
- **WHEN** Atlas Score is computed twice with the same system, draws, and scoring settings
- **THEN** both runs return the same numeric score and the same component breakdown

#### Scenario: Primary metric influences the score
- **WHEN** two systems differ only such that one has a strictly higher primary-metric count on the provided draws and coverage components are equal
- **THEN** the system with the higher primary-metric count receives the higher Atlas Score

### Requirement: Atlas Score reports components and formula version
The system SHALL report the score value, named component values, configured weights, and a formula version identifier when presenting an Atlas Score.

#### Scenario: Report includes components
- **WHEN** an Atlas Score report is produced
- **THEN** it includes the total score, at least primary and pairs components, and a formula version string

### Requirement: Atlas Score is historical and non-promotional
The system SHALL present Atlas Score as a historical diagnostic ranking signal and MUST NOT treat it as a prediction of future draws or as an automatic champion promotion decision.

#### Scenario: Non-predictive score report
- **WHEN** an Atlas Score CLI or report summary is produced
- **THEN** it states the score is historical only, does not predict the next draw, and does not auto-promote a champion
