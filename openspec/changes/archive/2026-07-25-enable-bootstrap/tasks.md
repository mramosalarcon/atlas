## 1. Config defaults

- [x] 1.1 Set `evaluation.freeze_policy.bootstrap.enabled: true` in `config/config.yaml`
- [x] 1.2 Confirm/tune shipped knobs (`n_resamples: 1000`, `ci_level: 0.95`, `seed: 42`, `min_ci_lower: 0`)
- [x] 1.3 Bump `freeze_policy.version` to a walk-forward-plus-bootstrap identifier

## 2. Loader and tests

- [x] 2.1 Reject `bootstrap.n_resamples < 1` at config load with a clear error
- [x] 2.2 Update config tests for enabled defaults, version string, and invalid n_resamples
- [x] 2.3 Confirm existing bootstrap gate unit test still passes

## 3. Smoke

- [x] 3.1 Run a compare or short tournament under enabled bootstrap; confirm CI appears in output and pytest passes
