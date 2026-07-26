## Why

Walk-forward freeze policy is live, but the optional paired bootstrap gate stays off (`enabled: false`, `min_ci_lower: 0`). With a ladder tournament and competing optimizers, accept decisions need a stricter confidence check so fold-pass luck alone cannot promote champions. The bootstrap code already exists; this change turns it on with documented Melate defaults and verifies behavior end-to-end.

## What Changes

- **Enable** freeze-policy bootstrap in shipped `config/config.yaml` with tuned defaults (`n_resamples`, `ci_level`, `seed`, `min_ci_lower`).
- Bump freeze-policy `version` string so experiment logs distinguish pre-/post-bootstrap accepts.
- Tighten config validation for bootstrap knobs where missing (e.g. `n_resamples >= 1`).
- Update tests and add a short smoke (compare or tournament) showing bootstrap CI in CLI output and gate behavior.
- Document that bootstrap is now part of the default accept path (operators can still disable it in YAML).
- Out of scope: new bootstrap algorithms, ROI as primary metric, changing fold count / required passes, dashboard.

## Capabilities

### New Capabilities
<!-- none — bootstrap capability already exists -->

### Modified Capabilities
- `config-manager`: Shipped defaults enable bootstrap; validate bootstrap numeric knobs clearly.
- `bootstrap-significance`: Document Melate default gate (`min_ci_lower`) and that enabled-by-default is the intended production posture.
- `strategy-comparison`: Freeze policy version reflects bootstrap-on defaults; compare/tournament reports always surface CI when enabled.

## Impact

- Mostly config + tests + light loader validation; reuses `atlas/evaluation/bootstrap.py` and existing compare wiring.
- **Behavioral change:** candidates that previously `accepted` on fold passes alone may now `rejected` when the bootstrap CI lower bound fails `min_ci_lower`.
- Tournament and `compare-systems` inherit the stricter gate automatically.
