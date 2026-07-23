## Context

ATLAS Core MVP already imports Melate history into an immutable SQLite raw DB and can evaluate/compare 8-ticket systems. `atlas/analytics/` exists but is empty. The PRD’s Sprint 2 envisioned Number Engine, Graph Engine, Atlas Baseline, and Scoring — this change delivers only the descriptive analytics slice needed before any score or optimizer.

Constraint carried forward: analytics are **diagnostics over history**, not predictors of future draws. Outputs and CLI text must say so.

## Goals / Non-Goals

**Goals:**

- Deterministic per-number profiles from the raw history (or a configured contest window).
- Pair co-appearance matrix for main numbers, queryable for top pairs.
- Draw-shape baseline summaries (sum, parity, decades, consecutives).
- Config-driven rolling window sizes and analytics storage paths.
- Rebuild-safe analytics persistence separate from the raw DB.
- CLI to build and inspect analytics.

**Non-Goals:**

- Atlas Score, Atlas Rating (ELO), ACI / confidence intervals.
- Graph community detection, triples/quads covering beyond pairs.
- Feeding analytics into freeze-policy accept/reject (comparison stays hit-coverage based).
- Optimizers, tournament, dashboard, Pandas/NetworkX dependencies.

## Decisions

1. **Compute from loaded `Draw` list, not SQL analytics columns in raw DB**  
   Keep raw DB immutable. Rebuild an analytics SQLite (or JSON exports) under `data/processed/`.

2. **Rolling windows are contest-count based, newest-first**  
   For window `N`, use the last `N` draws by ascending `CONCURSO`. Config list default: `[10, 20, 50, 100]`.

3. **Recency = contests since last main-number appearance**  
   If a number never appeared, recency is `null` (or a sentinel documented in the report). Additional appearances tracked separately from main hits.

4. **Co-appearance counts unordered pairs `{i,j}` from each draw’s six mains**  
   Matrix is symmetric; diagonal unused/zero. Rate = count / draws_in_window.

5. **Baseline stats are descriptive aggregates only**  
   Mean/median/min/max of main-number sum; average odd count; decade bucket occupancy (1–10 … 51–56); fraction of draws with at least one consecutive pair. No fitness scoring.

6. **Package layout: `atlas/analytics/`**  
   Modules e.g. `number_profiles.py`, `coappearance.py`, `baseline.py`, `store.py`. CLI wires through `atlas.cli`.

7. **Config additions under `analytics:`**  
   `rolling_windows`, `analytics_db` path, optional `export_dir`. Loader exposes typed `AnalyticsSettings`.

8. **No automatic coupling to strategy comparison**  
   Analytics may later inform human ticket design; they must not change accept/reject without a future change.

## Risks / Trade-offs

- **[Risk] Users interpret frequency/recency as predictive** → Mitigation: report headers and CLI banners state historical diagnostics only; specs forbid predictive claims.
- **[Risk] Overfitting windows tuned after peeking at validation** → Mitigation: document that analytics for strategy *design* should use train-window draws only when preparing candidates; CLI accepts optional contest range.
- **[Trade-off] Pairs only, not triples** → Enough for v1; triples deferred with Graph Engine.
- **[Trade-off] SQLite analytics vs pure in-memory** → Persist for CLI inspect/rebuild; in-memory compute first then save.

## Migration Plan

1. Extend config + loader.
2. Implement compute modules + unit tests on tiny draw fixtures.
3. Persist rebuild of analytics DB from raw history.
4. Add CLI commands; smoke on full Melate history.
5. No schema change to raw `draws` table; rollback = delete analytics DB files.

## Open Questions

- Whether default analytics build should restrict to train split automatically (default: full history, with optional `--until-contest` / train-only flag).
- Whether to export CSV alongside SQLite in v1 (default: SQLite + CLI text; CSV optional if cheap).
