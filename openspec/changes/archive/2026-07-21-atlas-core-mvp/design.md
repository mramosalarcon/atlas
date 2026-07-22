## Context

ATLAS is a Melate analytics system whose PRD requires: no strategy adopted without measurable out-of-sample improvement; evaluation must be fast and reproducible. The repo already has package layout (`atlas/domain`, `atlas/infrastructure`, `atlas/evaluation`, …), empty domain stubs, stub tests, and `data/raw/Melate.csv` (~4,238 contests: `CONCURSO`, `R1–R6`, `R7` adicional, `BOLSA`, `FECHA`).

This change implements Sprint 0–1 of the implementation plan as a thin vertical slice: config → domain → import/validate → evaluate → compare A vs B → experiment log. Optimizers, Atlas Score, graphs, and dashboard stay out.

## Goals / Non-Goals

**Goals:**

- Config-driven Melate rules (pool 1–56, 6 main + adicional, system size 8) with no game constants buried in code.
- Validated immutable raw history in SQLite from the existing CSV.
- Deterministic evaluation of any ticket and 8-ticket system (hits, prize-tier counts, coverage, configurable ROI).
- Objective A-vs-B comparison on a held-out validation window with a recorded accept/reject decision.
- Unit tests first on the evaluation core (TDD).

**Non-Goals:**

- Predicting future draws or claiming edge over pure chance.
- Atlas Score, Graph Engine, Ablation, Tournament, Ensemble.
- Multiple optimizers (even Greedy is deferred unless needed as a fixture generator).
- Streamlit dashboard, PDF reports, OR-Tools/NetworkX/scikit-learn.
- Full Melate prize-schedule accuracy beyond a configurable table (enough for reproducible ROI comparisons).

## Decisions

1. **Keep existing package layout; fill stubs rather than restructure**  
   Use `atlas/domain` for entities, `atlas/infrastructure` for CSV/SQLite, `atlas/evaluation` for evaluators and comparison, `config/` for YAML. Avoid inventing a parallel `engine/` tree from the Word plan until the core works.

2. **SQLite raw DB is append/rebuild-only; never update draw rows in place**  
   Import rebuilds or inserts only; analytics columns never live in the raw DB. Rationale: matches PRD RNF-07 and keeps the historical source of truth clean.

3. **stdlib `csv` + `sqlite3` for MVP; Pandas optional later**  
   History size (~4k rows) does not need Pandas. Prefer fewer dependencies and easier reproducibility.

4. **Domain is rules-agnostic via `LotteryRules`**  
   Validation and hit logic take rules from config (`min_number`, `max_number`, `main_count`, `system_size`). Melate-specific values live only in `config.yaml`.

5. **Primary comparison metrics: coverage of k-hit tiers + configurable ROI; not frequency scoring**  
   Fitness for later optimizers is out of scope, but A-vs-B comparison MUST optimize/compare combinatorial coverage and historical prize counts — not “hot numbers.” Document that historical ROI is a diagnostic under the rules of the game, not a forecast.

6. **Accept/reject rule (freeze policy) for MVP**  
   A candidate is accepted only if, on the validation window (default last 15% of contests by concurso order):  
   - primary metric (count of draws with ≥3 hits across the system) is strictly greater than baseline, **and**  
   - improvement is at least `min_absolute_delta` (default 1 draw) from config.  
   No p-value machinery in MVP; leave walk-forward / bootstrap for a later change. Record the rule version in the experiment log.

7. **Train/validation split by concurso order, not random shuffle**  
   Default 85% train / 15% validation by sorted `CONCURSO`. Test holdout can be reserved in config but unused in MVP comparison (validation only). Time-ordered split matches lottery chronology and the PRD intent.

8. **CLI as a thin module**  
   Entry points: `import-history`, `evaluate-system`, `compare-systems`. No web UI.

9. **Prize table in config**  
   Map hit tiers (3/4/5/6 + adicional rules if needed) to amounts; if unknown, use placeholder amounts flagged in config so ROI is still comparable between strategies.

## Risks / Trade-offs

- **[Risk] Historical metrics look like prediction** → Mitigation: CLI/report text states ATLAS compares strategies on history; it does not predict draws. Specs forbid predictive claims in outputs.
- **[Risk] Overfitting via tuning comparison windows** → Mitigation: windows and accept thresholds live in versioned config; experiment log stores the config hash/path used.
- **[Risk] Incomplete/incorrect Melate prize rules for ROI** → Mitigation: treat ROI as secondary; primary accept metric is hit-tier coverage counts; prize table is clearly configurable.
- **[Risk] Empty stubs tempt large refactors** → Mitigation: implement only what specs require; leave unused packages empty.
- **[Trade-off] Simple delta threshold vs statistical significance** → Accept for MVP speed; document upgrade path to bootstrap/walk-forward in Open Questions.

## Migration Plan

1. Add `config/config.yaml` and loaders.
2. Implement domain + tests (ticket hits, validation).
3. Import CSV → SQLite; fail closed on invalid rows.
4. Wire system evaluation + report dict/text.
5. Wire compare + experiment log (SQLite table or JSONL under `data/processed/`).
6. No production deploy; local CLI only. Rollback = delete generated DB/log files; CSV untouched.

## Open Questions

- Exact Melate prize amounts and adicional rules for ROI — confirm or keep placeholders.
- Whether validation must also require non-regression on train (optional guardrail).
- Preferred experiment log format: SQLite table vs JSONL (default: SQLite `experiments` table beside raw DB, separate file).
