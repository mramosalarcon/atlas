## MODIFIED Requirements

### Requirement: Covering optimizer builds tickets from priority pairs
The system SHALL provide a covering-design optimizer that constructs `system_size` tickets by repeatedly selecting numbers to cover high-priority still-uncovered unordered **k-tuples** for each configured cover order `k ∈ {2, 3, 4}` (including pairs when `2` is enabled) until each ticket has `main_count` numbers.

#### Scenario: Empty ticket seeds from top uncovered tuple
- **WHEN** a new ticket is empty and uncovered priority tuples remain for an enabled cover order
- **THEN** the optimizer seeds the ticket with the numbers of the highest-scoring uncovered tuple (ties broken by preferring larger `k`, then lexicographic tuple order)

#### Scenario: Subsequent numbers extend multi-order coverage
- **WHEN** a ticket already contains at least one number and needs more numbers
- **THEN** the next number chosen maximizes the total effective priority of uncovered tuples (across enabled cover orders) that would become newly covered by adding that number (ties broken by smallest number)

## ADDED Requirements

### Requirement: Cover orders include triples and optional quads
The system SHALL support cover orders 2 (pairs), 3 (triples), and 4 (quads) as configured, and MUST include order 2 in any valid covering configuration.

#### Scenario: Default includes pairs and triples
- **WHEN** covering runs with default Melate covering config
- **THEN** construction considers at least pairs and triples when scoring seeds and growth steps

#### Scenario: Quads optional
- **WHEN** config includes `4` in `cover_orders`
- **THEN** construction also tracks and scores uncovered 4-tuples

### Requirement: Per-order relative weights scale tuple priority
The system SHALL multiply each tuple’s base weight by a configured per-order relative weight when ranking seeds and growth candidates.

#### Scenario: Higher order weight prefers that order on ties of base weight
- **WHEN** two uncovered tuples have equal base weight but different order relative weights
- **THEN** the tuple with the larger effective weight (`order_weight[k] * base`) is preferred

### Requirement: Covered tuples are removed after each ticket
The system SHALL, after completing each ticket, remove every enabled-order k-tuple fully contained in that ticket from the uncovered maps before building the next ticket.

#### Scenario: Next ticket ignores already covered triples
- **WHEN** a completed ticket contains triple `{1,2,3}` and order 3 is enabled
- **THEN** subsequent ticket construction does not treat `{1,2,3}` as still uncovered

### Requirement: Covering search remains deterministic
The system SHALL produce identical ticket systems given identical draws, rules, seed, and covering settings (including cover orders and order weights).

#### Scenario: Same inputs reproduce the system
- **WHEN** covering optimize is run twice with the same inputs and settings
- **THEN** both runs return identical ordered ticket number lists

### Requirement: Covering reports include higher-order coverage counts
The system SHALL include covered pair, triple, and (when applicable) quad counts in covering optimize reports while remaining a non-predictive comparison candidate.

#### Scenario: Report lists triple coverage
- **WHEN** a covering optimize report is produced with triples enabled
- **THEN** the report includes an unordered triple coverage count and states the system does not predict the next draw
