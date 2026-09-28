## ADDED Requirements

### Requirement: Fold-robust supports a champion-relative train objective
The system SHALL support a fold-robust objective mode `relative` that scores candidate systems on the provided train draws by per-fold primary-metric deltas against a fixed baseline `TicketSystem`, using the same contiguous fold partition and primary min-hits as absolute fold-robust search.

#### Scenario: Relative mode uses baseline fold deltas
- **WHEN** fold-robust optimize runs with objective `relative` and a valid baseline system
- **THEN** each fold score contribution is `candidate_primary − baseline_primary` on that train fold

#### Scenario: Absolute mode remains available
- **WHEN** fold-robust optimize runs with objective `absolute` (or the default)
- **THEN** scoring uses the existing absolute min-fold / sum-fold / aggregate / coverage lexicographic order and does not require a relative baseline

### Requirement: Relative objective prefers freeze-aligned fold passes then sum of deltas
When objective is `relative`, the system SHALL rank neighboring systems lexicographically by (1) count of train folds whose delta is ≥ `evaluation.min_absolute_delta`, (2) sum of fold deltas, then (3) the absolute fold-robust tie-breakers (min fold primary, sum of fold primaries, aggregate primary, pairs, triples, quads).

#### Scenario: Extra train fold pass is preferred
- **WHEN** a legal move increases the count of train folds with delta ≥ `min_absolute_delta`
- **THEN** the move is accepted even if absolute min-fold primary is unchanged or slightly lower

#### Scenario: Sum of deltas breaks a pass-count tie
- **WHEN** two neighbors share the same train fold-pass count and one has a strictly greater sum of fold deltas
- **THEN** relative search prefers the greater sum of deltas

### Requirement: Relative baseline path is resolved and validated
The system SHALL resolve the relative baseline from CLI `--relative-to`, else `optimizer.fold_robust.relative_to`, else `optimizer.fold_robust.seed_from`, else `tournament.champion`, and SHALL fail clearly if relative mode is selected and no readable baseline ticket-system JSON is available.

#### Scenario: Missing baseline fails clearly
- **WHEN** objective is `relative` and no baseline path resolves to an existing ticket-system file
- **THEN** optimize fails with an error naming the missing baseline and does not export a candidate

### Requirement: Fold-robust report names relative objective diagnostics
When objective is `relative`, the system SHALL include the objective mode, baseline identity/path, per-fold train deltas, and train fold-pass count in the optimize report while remaining a non-predictive comparison candidate.

#### Scenario: Report shows relative diagnostics
- **WHEN** a relative fold-robust report is produced
- **THEN** the report identifies relative mode, the baseline used, and per-fold train deltas

## MODIFIED Requirements

### Requirement: Fold-robust optimizer seeds from covering then polishes for fold stability
The system SHALL provide a fold-robust optimizer that constructs an initial `TicketSystem` either via the covering optimizer on the provided draw set or via an optional seed ticket-system file, then applies deterministic single-ticket number-replacement moves scored by the configured fold-robust objective (`absolute` or `relative`) until no improving move remains within the configured pass budget.

#### Scenario: Returns a full valid system
- **WHEN** fold-robust optimize completes successfully
- **THEN** the result contains exactly `system_size` valid tickets under the provided rules

#### Scenario: Uses only provided draws
- **WHEN** fold-robust optimize runs
- **THEN** search uses only the draw set passed into optimize and does not read validation or holdout draws (file seeding and relative baseline load tickets only, not extra history)

#### Scenario: Same inputs reproduce the system for a given seed mode
- **WHEN** fold-robust optimize is run twice with the same draws, rules, settings, fold count, objective mode, baseline (when relative), and seed path (or covering mode)
- **THEN** both runs return identical ordered ticket number lists
