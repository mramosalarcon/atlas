## 1. Config extensions

- [x] 1.1 Add `analytics` section to `config/config.yaml` (rolling windows `[10,20,50,100]`, analytics DB path under `data/processed/`)
- [x] 1.2 Extend typed settings + loader for analytics settings; fail clearly if analytics is requested but section missing
- [x] 1.3 Add/adjust config tests for analytics windows and missing-section error

## 2. Number profiles

- [x] 2.1 Implement number profile computation (total main frequency, rolling windows newest-first, recency, additional counts) for full number range
- [x] 2.2 Add unit tests for window counting, never-appeared recency null, and deterministic rebuild
- [x] 2.3 Format number profile report text with explicit non-prediction disclaimer

## 3. Co-appearance matrix

- [x] 3.1 Implement unordered pair co-appearance counts (and rates) over a draw set
- [x] 3.2 Implement deterministic top-N pairs reporting
- [x] 3.3 Add unit tests for single-draw pair increments, rates, and top-N tie-break order

## 4. Draw baseline

- [x] 4.1 Implement baseline summaries: sum min/max/mean/median, mean odd count, decade occupancy averages, consecutive-pair fraction
- [x] 4.2 Add unit tests for sum stats and consecutive-pair detection on fixture draws
- [x] 4.3 Format baseline report as historical reference only (non-predictive language)

## 5. Persistence and CLI

- [x] 5.1 Persist rebuilt analytics (profiles, pairs, baseline metadata) to configured analytics SQLite without modifying the raw DB
- [x] 5.2 Add CLI commands: `build-analytics`, `show-number`, `show-pairs`, `show-baseline`
- [x] 5.3 Smoke on full imported Melate history; confirm raw DB unchanged and pytest passes
