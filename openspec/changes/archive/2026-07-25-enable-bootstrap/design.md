## Context

Paired bootstrap over walk-forward fold deltas is already implemented and wired into `compare_systems`, but shipped config keeps `bootstrap.enabled: false`. Operators now run ladders with multiple challengers; enabling the CI gate reduces false promotions from fold-pass noise. With only `n_folds=5` deltas, CIs are wide—defaults must be honest about that.

## Goals / Non-Goals

**Goals:**

- Turn bootstrap on in default Melate config with explicit tuned knobs.
- Version the freeze policy so experiment history can tell bootstrap-era decisions apart.
- Validate bootstrap settings at load time (`n_resamples >= 1`, existing `ci_level` checks).
- Confirm CLI/tournament surfaces CI and that the gate can reject otherwise fold-passing candidates.
- Keep disable-via-config as an escape hatch.

**Non-Goals:**

- Replacing percentile bootstrap with BCa or parametric tests.
- Changing `n_folds` / `required_fold_passes` / primary metric.
- Auto-tuning `min_ci_lower` from data.
- Persisting a new experiment table.

## Decisions

1. **Default gate: `enabled: true`, `min_ci_lower: 0`**  
   Require the bootstrap CI lower bound on mean fold-delta to be ≥ 0 (non-negative mean-delta evidence at the configured CI level).  
   Alternative considered: `min_ci_lower: 1` aligned with `min_absolute_delta` — too harsh with only 5 folds; start at 0 and raise later if accepts stay noisy.

2. **Resamples / CI**  
   Keep `n_resamples: 1000`, `ci_level: 0.95`, `seed: 42` (already present). Optional later bump to 2000 if variance of bounds matters; not required for v1 enable.

3. **Policy version**  
   Set `freeze_policy.version` to `walkforward-v1+bootstrap` (or `walkforward-bootstrap-v1`) when shipping enabled defaults so `list-experiments` / evidence JSON show the era. Loader continues to accept an explicit version override in YAML.

4. **No algorithm changes**  
   Keep `paired_bootstrap_ci` as-is (seeded percentile CI over mean of resampled fold deltas).

5. **Tests / smoke**  
   Update default-config assertions (`enabled is True`). Keep unit test that forces reject via high `min_ci_lower`. Smoke: one `compare-systems` or short `run-tournament` with bootstrap printed.

## Risks / Trade-offs

- **[Risk] Stricter gate overturns current champion narrative** → Mitigation: expected; re-run tournament after enable; document in summary.
- **[Risk] Wide CI with 5 folds rejects almost everyone** → Mitigation: `min_ci_lower: 0` not higher; operators may temporarily disable bootstrap in YAML.
- **[Risk] Historical experiments mixed eras** → Mitigation: version string bump in evidence.
- **[Trade-off] Enable without changing fold design** → Prefer operational enable now; fold redesign is a separate change.

## Migration Plan

1. Edit `config/config.yaml` (enable + version).
2. Loader validation for `n_resamples`.
3. Update config/comparison tests; smoke compare/tournament.
4. No DB migration.

## Open Questions

- Whether to raise `min_ci_lower` toward `min_absolute_delta` after observing a few post-enable tournaments.
- Whether tournament summary should echo bootstrap CI per duel (CLI compare already prints it; ladder summary currently shows fold passes only — optional enhancement if smoke shows operators need it).
