## 1. Config

- [x] 1.1 Add `evaluation.freeze_policy` settings to `config/config.yaml` (`n_folds`, `required_fold_passes`, bootstrap block)
- [x] 1.2 Extend typed settings + loader with validation (`n_folds` >= 2, `required_fold_passes` <= `n_folds`)
- [x] 1.3 Add config tests for defaults and invalid freeze-policy combinations

## 2. Walk-forward evaluation

- [x] 2.1 Implement contiguous chronological fold partitioning covering all draws
- [x] 2.2 Evaluate baseline vs candidate primary metrics per fold and mark pass/fail vs `min_absolute_delta`
- [x] 2.3 Add unit tests for fold partition coverage and pass/fail marking

## 3. Bootstrap significance (optional gate)

- [x] 3.1 Implement seeded paired bootstrap over fold deltas with percentile CI
- [x] 3.2 Wire bootstrap gate into accept logic when enabled; skip when disabled
- [x] 3.3 Add tests for reproducibility and reject-when-CI-fails

## 4. Comparison + experiment persistence

- [x] 4.1 Update `compare_systems` to decide via walk-forward (+ bootstrap) while still recording holdout diagnostics
- [x] 4.2 Persist policy version and fold/bootstrap evidence in the experiment store (additive schema)
- [x] 4.3 Update CLI compare output to show fold pass counts and bootstrap summary when present
- [x] 4.4 Update comparison tests for accept/reject under multi-fold policy; confirm pytest passes
