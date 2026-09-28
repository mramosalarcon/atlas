## 1. Config

- [x] 1.1 Add `evaluation.min_contest: 2088` to shipped `config/config.yaml`
- [x] 1.2 Extend `EvaluationSettings` + loader (`int | None`, reject values `< 1`)
- [x] 1.3 Add config tests for default 2088, omitted/null = no floor, and invalid values

## 2. Filtered draw loading

- [x] 2.1 Add helper to load draws with optional `min_contest` without mutating raw DB/CSV
- [x] 2.2 Wire evaluate / optimize / compare / tournament / score CLI paths to filtered loads
- [x] 2.3 Fail clearly when filtered window is empty or too small for validation/freeze folds
- [x] 2.4 Keep `import-history` (and analytics v1) on full history

## 3. Tests and operator smoke

- [x] 3.1 Unit tests: filter excludes contests `< min_contest`; import still stores full history
- [x] 3.2 Smoke: with `min_contest=2088`, regenerate one optimizer candidate and confirm reported contests are `>= 2088`
- [x] 3.3 Confirm pytest passes
