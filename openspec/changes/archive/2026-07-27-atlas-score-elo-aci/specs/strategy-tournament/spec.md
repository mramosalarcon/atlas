## ADDED Requirements

### Requirement: Tournament may update Elo ratings after duels
The system SHALL allow a tournament run to optionally update Atlas Ratings from each duel’s freeze-policy decision, and MUST NOT change champion promotion rules based on ratings.

#### Scenario: Opt-in rating update after duel
- **WHEN** a tournament is run with rating updates enabled and a duel decision is recorded
- **THEN** Elo ratings for champion and challenger identities are updated from that decision

#### Scenario: Promotion ignores ratings
- **WHEN** a challenger has a higher Elo rating than the champion but the freeze decision is `rejected`
- **THEN** the champion is not replaced
