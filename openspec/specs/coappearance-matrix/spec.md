## Purpose

Build and report main-number pair co-appearance counts and rates as historical diagnostics.

## Requirements

### Requirement: Build main-number pair co-appearance matrix
The system SHALL count how often each unordered pair of distinct main numbers co-occurs in the same draw over a specified draw set, producing a symmetric matrix (or equivalent pair map) for all numbers in the configured range.

#### Scenario: Pair counted once per draw
- **WHEN** a draw contains mains `{1,2,3,4,5,6}`
- **THEN** the pair `{1,2}` is incremented exactly once for that draw (not once per ordering)

#### Scenario: Top pairs report
- **WHEN** a caller requests the top `N` co-appearing pairs
- **THEN** the system returns the `N` pairs with highest co-appearance counts (ties broken deterministically, e.g. by ascending pair order)

### Requirement: Co-appearance outputs are diagnostic only
The system SHALL expose co-appearance counts and optional rates (count / draws) as historical diagnostics and MUST NOT label them as predictions.

#### Scenario: Rate definition
- **WHEN** pair `{i,j}` co-appeared `c` times in `D` draws
- **THEN** the reported rate is `c / D` (0 when `D=0` is rejected as invalid input rather than silently yielding NaN)
