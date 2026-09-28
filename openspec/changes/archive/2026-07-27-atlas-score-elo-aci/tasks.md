## 1. Config

- [x] 1.1 Add `scoring` section to `config/config.yaml` (weights, elo, aci paths/knobs)
- [x] 1.2 Extend typed settings + loader validation (positive K, valid ACI resamples/ci_level)
- [x] 1.3 Add config tests for defaults and invalid scoring settings

## 2. Atlas Score

- [x] 2.1 Implement deterministic Atlas Score (`atlas-score-v1`) with component breakdown on a provided draw set
- [x] 2.2 Add CLI `score-system` with window selection (holdout/train/all) and non-predictive report
- [x] 2.3 Add unit tests for determinism and primary-metric dominance when coverage ties

## 3. ACI

- [x] 3.1 Implement bootstrap ACI for a single-system Atlas Score (seeded, percentile bounds)
- [x] 3.2 Implement pairwise ACI for score deltas on shared resample indices
- [x] 3.3 Add CLI to report ACI; unit tests for seed reproducibility

## 4. Atlas Rating (Elo)

- [x] 4.1 Implement Elo update + SQLite (or configured) ratings persistence by system identity
- [x] 4.2 Add CLI to list ratings and apply updates from a comparison decision / experiment
- [x] 4.3 Add unit tests for accept/reject rating direction and persistence across reopen

## 5. Integration hooks

- [x] 5.1 Optionally attach Score/ACI diagnostics to compare-systems report without changing decisions
- [x] 5.2 Optionally update ratings from `run-tournament` when a flag is set; promotion unchanged
- [x] 5.3 Smoke Score/ACI/ratings on current champion export; confirm pytest passes
