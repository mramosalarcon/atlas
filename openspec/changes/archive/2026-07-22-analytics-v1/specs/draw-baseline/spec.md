## ADDED Requirements

### Requirement: Compute draw-shape baseline summaries
The system SHALL compute descriptive baseline statistics over a specified draw set for: main-number sum (min, max, mean, median), mean count of odd main numbers, decade occupancy averages for buckets covering the configured number range, and the fraction of draws containing at least one consecutive main-number pair.

#### Scenario: Sum summary on tiny history
- **WHEN** baseline is computed on draws whose main sums are known
- **THEN** reported min, max, mean, and median match those sums

#### Scenario: Consecutive pair detection
- **WHEN** a draw's mains include at least one pair of values differing by 1
- **THEN** that draw counts as having a consecutive pair for the baseline fraction

### Requirement: Baseline is reference-only
The system SHALL present draw baselines as historical reference descriptors and MUST NOT use them to auto-accept or reject strategies in this change.

#### Scenario: Report language
- **WHEN** a baseline report is generated
- **THEN** it describes historical draw shape under game rules and does not claim knowledge of the next draw
