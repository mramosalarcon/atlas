## Why

Absolute fold-robust search (maximize min/sum of fold primaries) has stalled at 2/5 freeze-policy fold passes against the local-search champion—even when seeded from that champion. Search is optimizing the wrong signal: freeze policy cares about **per-fold deltas vs the baseline**, not absolute train primary. Operators need a train-only objective aligned with that gate without lowering promotion thresholds.

## What Changes

- Add an optional **champion-relative** fold-robust objective mode that scores candidate systems using per-fold primary deltas against a fixed baseline `TicketSystem` (typically the tournament champion), using the same contiguous fold partition and primary metric as freeze-policy walk-forward on the **train** draw set.
- Lexicographic preference: count of folds with delta ≥ `min_absolute_delta`, then sum of fold deltas, then existing absolute fold-robust / coverage tie-breakers as designed.
- Config + CLI: select objective mode and baseline path (default: champion / `seed_from` / explicit `--relative-to`); absolute mode remains the default for reproducibility of prior candidates.
- Report mode, baseline identity, and per-fold train deltas; still train-only; no auto-accept; freeze policy unchanged.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `fold-robust-optimizer`: Optional champion-relative train objective alongside absolute fold-robust scoring; report relative diagnostics.
- `config-manager`: Load fold-robust objective mode and optional relative-baseline path settings.

## Impact

- `atlas/optimization/fold_robust.py` scoring/hill climb, CLI `optimize-fold-robust`, config YAML/settings/loader, unit/smoke tests vs current champion under freeze policy.
- Freeze policy, tournament, bootstrap, and `min_contest` unchanged. Promotion remains empirical.
