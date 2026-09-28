## Context

Fold-robust hill climb already exists with covering as the only seed. Against the sticky local-search champion under `min_contest=2088`, covering-seeded fold-robust improved holdout but failed freeze (2/5 folds). Starting from the champion tickets should keep fold strength while allowing fold-aware polish to accept only moves that improve `(min_fold, sum_fold, …)`.

## Goals / Non-Goals

**Goals:**

- Optional seed-from JSON path for fold-robust (`optimizer.fold_robust.seed_from`).
- Null/omit → covering seed (current behavior).
- Ship Melate default pointing at tournament champion export.
- CLI override `--seed-from` for one-off runs.
- Report seed source; train-only; no auto-accept.

**Non-Goals:**

- Changing fold-robust objective, freeze thresholds, or tournament sticky rules.
- Automatically updating `tournament.champion` after optimize.
- Guaranteeing promotion (empirical).
- Seeding other optimizers in this change.

## Decisions

1. **Config field `seed_from: Path | null`**  
   ```yaml
   optimizer:
     fold_robust:
       enabled: true
       max_passes: 20
       seed_from: data/exports/local_search_candidate.json  # null = covering
   ```  
   Resolved relative to project root like other paths.  
   Alternative: enum `seed_source: covering|champion` only — rejected; explicit path is clearer and testable without requiring tournament section.

2. **CLI `--seed-from` overrides config**  
   When provided, load that file; else use config `seed_from`; else covering.

3. **Load seed as `TicketSystem` under lottery rules**  
   Reuse existing system JSON loader used by evaluate/compare. Fail clearly if file missing, invalid, or wrong `system_size`.

4. **Hill climb unchanged**  
   Same fold-robust score and neighborhood; only the initial system changes. If no improving move exists, export equals the seed (valid candidate).

5. **Report**  
   Include `Seed: covering` or `Seed: <path>` (and system name) so operators know which path ran.

## Risks / Trade-offs

- **[Risk] Seed equals champion → compare rejects as no improvement / 0 delta folds** → Mitigation: still useful diagnostic; optional more `max_passes`; accept that polish may be null.
- **[Risk] Stale champion file after regenerate** → Mitigation: document regenerate local-search before fold-robust when chaining.
- **[Trade-off] Couples optimize default to tournament export path** → Accept; override with null or `--seed-from`.

## Migration Plan

1. Add settings/loader + optimizer seed branch + CLI flag.
2. Update shipped config `seed_from` to champion path.
3. Operator: `optimize-fold-robust` → `--compare-baseline` / `run-tournament`.
4. Rollback: set `seed_from: null` to restore covering seed.

## Open Questions

- Whether default should track `tournament.champion` automatically when `seed_from` is a sentinel (lean: no; explicit path in v1).
