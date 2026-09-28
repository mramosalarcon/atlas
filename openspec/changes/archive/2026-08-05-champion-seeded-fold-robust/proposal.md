## Why

Fold-robust currently seeds from covering and lost freeze policy against the sticky local-search champion (2/5 folds). Operators want a stronger challenger that starts from the proven champion ticket set and only accepts fold-robust moves that improve worst-fold stability—without lowering freeze thresholds.

## What Changes

- Allow fold-robust optimize to seed from a configured/exported ticket-system JSON (default remains covering when unset).
- Ship Melate default to seed from `tournament.champion` (or an explicit `optimizer.fold_robust.seed_from` path) so polish starts at the current champion.
- Report the seed source in the fold-robust optimize output; still train-only search; no auto-accept.
- Keep covering seed available for reproducibility of prior fold-robust candidates.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `fold-robust-optimizer`: Support optional file/champion seed before fold-aware hill climb; covering remains the fallback seed.
- `config-manager`: Load optional `optimizer.fold_robust.seed_from` path (null/omit = covering seed).

## Impact

- `FoldRobustOptimizer` seeding path, CLI `optimize-fold-robust`, config YAML/settings/loader, unit tests, and smoke compare vs current champion under freeze policy.
- Freeze policy, tournament rules, and `min_contest` unchanged. Promotion remains empirical.
