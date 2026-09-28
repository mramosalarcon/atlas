## ADDED Requirements

### Requirement: Systems have Elo ratings updated from freeze-policy duel outcomes
The system SHALL maintain an Elo-style rating per system identity and update ratings when a freeze-policy comparison decision is applied as a duel outcome (`accepted` or `rejected`), using configured initial rating and K-factor.

#### Scenario: Accepted challenger gains rating against champion
- **WHEN** a challenger is `accepted` against a champion baseline and ratings are updated
- **THEN** the challenger’s rating increases and the champion’s rating decreases according to the Elo update rule

#### Scenario: Rejected challenger loses rating against champion
- **WHEN** a challenger is `rejected` against a champion baseline and ratings are updated
- **THEN** the challenger’s rating decreases and the champion’s rating increases according to the Elo update rule

### Requirement: Ratings persist across runs
The system SHALL persist ratings to a configured store so subsequent rating updates and listings reuse prior values instead of resetting to the initial rating each process start.

#### Scenario: Rating survives process restart
- **WHEN** a rating is updated and later listed in a new process using the same ratings store
- **THEN** the listed rating matches the persisted value

### Requirement: Rating reports are non-predictive
The system SHALL present Atlas Ratings as historical duel-derived rankings and MUST NOT claim they predict future draws or replace freeze-policy promotion.

#### Scenario: Non-predictive ratings report
- **WHEN** a ratings list or update summary is produced
- **THEN** it states ratings reflect historical freeze-policy duel outcomes and do not predict the next draw
