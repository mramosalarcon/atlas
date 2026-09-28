## 1. Analytics contest floor

- [x] 1.1 Wire `build-analytics` to load draws with `evaluation.min_contest` and fail clearly if empty
- [x] 1.2 Print contest floor / contest range on successful analytics rebuild
- [x] 1.3 Unit or CLI-level tests: analytics inputs exclude contests `< min_contest`; import untouched

## 2. Experiment min_contest persistence

- [x] 2.1 Add nullable `min_contest` column to experiments schema (migrate existing DBs)
- [x] 2.2 Write `min_contest` from config on compare/tournament experiment append; include in `policy_evidence`
- [x] 2.3 Surface `min_contest` in `list-experiments` (and record type)
- [x] 2.4 Tests: floor stored when set; null when omitted; list shows stored value

## 3. Verification

- [x] 3.1 Smoke: rebuild analytics under `min_contest=2088` and confirm reported window
- [x] 3.2 Smoke: one compare stores `min_contest=2088` in experiments
- [x] 3.3 Confirm pytest passes
