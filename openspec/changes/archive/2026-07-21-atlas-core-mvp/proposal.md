## Why

ATLAS needs an objective way to compare 8-ticket Melate strategies on real history before any optimizer or scoring layer can be trusted. The repo has empty domain stubs and a Melate CSV (~4,238 draws), but no working import, evaluation, or out-of-sample comparison loop yet. Building this thin core now freezes the "arbiter" so later analytics and optimization are measurable.

## What Changes

- Add config-driven Melate rules and project settings (`config.yaml`) with no hardcoded game constants in business logic.
- Implement domain types (`Draw`, `Ticket`, `TicketSystem`, `LotteryRules`, evaluation results) with validation and unit tests.
- Import and validate `data/raw/Melate.csv` into an immutable SQLite raw database.
- Evaluate any 8-ticket system against the full history (hits 3/4/5/6, coverage, basic ROI) in under 1 second.
- Compare strategy A vs B with train/validation split and an experiment log that records accept/reject decisions.
- Ship a minimal CLI (or Python entrypoint) to import, evaluate, and compare — no dashboard, graph engine, multi-algorithm tournament, or ensemble in this change.

## Capabilities

### New Capabilities
- `config-manager`: Load and expose Melate rules, evaluation windows, and fitness/report weights from external config.
- `draw-import`: Parse Melate CSV, validate contests, and persist an immutable raw SQLite history.
- `system-evaluation`: Score a single ticket and an 8-ticket system against draws (hits, prize tiers, coverage, ROI).
- `strategy-comparison`: Compare two systems out of sample and record experiments with an explicit accept/reject rule.

### Modified Capabilities
- (none — no existing specs in `openspec/specs/`)

## Impact

- Fills in existing empty packages under `atlas/domain/`, `atlas/infrastructure/`, `atlas/evaluation/`, and `tests/`.
- Uses `data/raw/Melate.csv` as the initial source of truth; adds `data/processed/` or a SQLite file for the raw DB.
- Adds `config/` with Melate rules; introduces dependencies likely limited to Python stdlib + pytest (Pandas/SQLite only if needed for import speed).
- Explicitly out of scope: Atlas Score, Graph Engine, optimizers, Tournament/Ensemble, Streamlit dashboard, ACI intervals.
