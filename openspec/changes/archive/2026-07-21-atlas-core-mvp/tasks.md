## 1. Project setup and config

- [x] 1.1 Add minimal project packaging (`pyproject.toml` or requirements) with pytest; keep deps to stdlib + PyYAML + pytest
- [x] 1.2 Create `config/config.yaml` with Melate rules (1–56, main_count=6, system_size=8), validation_ratio, min_absolute_delta, prize table placeholders, and paths
- [x] 1.3 Implement config loader that fails clearly on missing path and returns a typed rules/settings object used by domain code

## 2. Domain model (TDD)

- [x] 2.1 Implement `LotteryRules` and domain exceptions; replace empty stubs
- [x] 2.2 Implement `Draw` and `Ticket` with validation (range, uniqueness, ascending mains, correct length)
- [x] 2.3 Implement ticket hit counting against a draw (main hits; adicional flag as needed)
- [x] 2.4 Implement `TicketSystem` enforcing configured system size
- [x] 2.5 Replace stub tests in `tests/test_ticket.py` with real cases (3 hits, 4 hits, perfect match, invalid ticket)

## 3. Draw import and raw SQLite

- [x] 3.1 Implement CSV parser for Melate columns (`CONCURSO`, `R1`–`R6`, `R7`, `FECHA`, optional `BOLSA`)
- [x] 3.2 Implement validation pipeline: range, duplicates, ascending order, unique contests, contiguous concurso sequence
- [x] 3.3 Persist validated draws to SQLite raw DB (rebuild-safe); never modify `data/raw/Melate.csv`
- [x] 3.4 Add import tests with small fixture CSVs for success and each failure mode

## 4. System evaluation

- [x] 4.1 Implement system evaluator over a draw list: per-draw best hits, 3/4/5/6 tier aggregates, coverage summary
- [x] 4.2 Compute ROI from config prize table + ticket cost; document placeholders if amounts are provisional
- [x] 4.3 Ensure evaluation report/result text does not claim future-draw prediction
- [x] 4.4 Add unit tests for system-size enforcement, deterministic results, and aggregate counts
- [x] 4.5 Benchmark full-history evaluation of one 8-ticket system against imported Melate data; confirm &lt; 1s

## 5. Strategy comparison and experiment log

- [x] 5.1 Implement chronological train/validation split from config (`validation_ratio` by concurso order)
- [x] 5.2 Implement compare(baseline, candidate) on validation window with primary metric and clear improved/tied/worsened outcome
- [x] 5.3 Apply freeze policy: accept only if validation primary metric improves by ≥ `min_absolute_delta`; else reject
- [x] 5.4 Persist experiment records (timestamp, systems, window, metrics, delta, decision, threshold) and support listing them
- [x] 5.5 Add tests for accept, reject, and that rejected comparisons are still logged

## 6. CLI entrypoints and smoke verification

- [x] 6.1 Add CLI/module commands: `import-history`, `evaluate-system`, `compare-systems`
- [x] 6.2 Run end-to-end smoke: import real `Melate.csv` → evaluate a sample 8-ticket system → compare two systems → show experiment log
- [x] 6.3 Confirm all new tests pass with pytest
