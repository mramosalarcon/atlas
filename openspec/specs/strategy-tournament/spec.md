## Purpose

Schedule ladder challenges of frozen 8-ticket system exports against a sticky champion under freeze-policy comparison.

## Requirements

### Requirement: Ladder tournament challenges a sticky champion
The system SHALL run a ladder tournament that loads a champion system and an ordered list of challenger systems, then compares each challenger against the current champion using the existing freeze-policy comparison path.

#### Scenario: Each challenger faces the current champion once
- **WHEN** a ladder tournament starts with a champion and N challengers
- **THEN** the system performs exactly N freeze-policy comparisons in challenger order, each using the champion active at that step as baseline

#### Scenario: Accepted challenger becomes champion
- **WHEN** a challenger comparison decision is `accepted`
- **THEN** that challenger becomes the champion for all subsequent duels in the same tournament run

#### Scenario: Rejected challenger leaves champion unchanged
- **WHEN** a challenger comparison decision is `rejected`
- **THEN** the champion remains the same for the next duel

### Requirement: Tournament uses freeze policy as sole promotion gate
The system SHALL promote or retain the champion solely from freeze-policy compare decisions and MUST NOT promote based on holdout diagnostic delta alone.

#### Scenario: Holdout-improved but rejected does not promote
- **WHEN** a challenger’s holdout diagnostic improves but the freeze decision is `rejected`
- **THEN** the champion is not replaced

### Requirement: Tournament summary is reported and optionally exported
The system SHALL print a tournament summary including tournament id, initial champion, duel outcomes (challenger name, decision, fold passes), and final champion, and MUST state that results are historical comparisons that do not predict future draws. When an output path is provided, the system SHALL write the same summary as JSON.

#### Scenario: Summary lists final champion
- **WHEN** the tournament completes
- **THEN** the summary identifies the final champion system name or path

#### Scenario: Non-predictive banner
- **WHEN** a tournament summary is produced
- **THEN** it states the run is historical freeze-policy comparison and does not predict the next draw

### Requirement: Each duel is logged as an experiment
The system SHALL persist each ladder duel through the existing experiment store so rejected and accepted comparisons remain listable after the tournament.

#### Scenario: Experiments exist for every duel
- **WHEN** a tournament with N challengers completes successfully
- **THEN** N experiment records exist corresponding to those comparisons
