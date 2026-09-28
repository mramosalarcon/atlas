## Context

`evaluation.min_contest` filters evaluation draw loads. Analytics CLI still calls unfiltered `load_draws`, and experiment rows only imply the window via validation contest range and config path. This follow-up aligns analytics with the evaluation floor and makes the floor auditable on experiment records.

## Goals / Non-Goals

**Goals:**

- Analytics build/show use draws with `contest >= min_contest` when configured (same helper filter as evaluation loads).
- Persist `min_contest` on every new experiment record; expose it when listing/reading experiments.
- Clear operator note when analytics rebuild applies a floor; fail clearly if filtered analytics window is empty.
- Keep import and raw DB full-history.

**Non-Goals:**

- Changing freeze policy, optimizer objectives, or default Melate floor value.
- Backfilling historical experiment rows with guessed floors.
- Dual analytics stores (full vs filtered); one rebuild replaces analytics DB contents for the active window.
- Truncating CSV.

## Decisions

1. **Reuse `load_draws(..., min_contest=)` for analytics**  
   CLI `build-analytics` passes `config.evaluation.min_contest`. Show commands read stored analytics (already built for that window after rebuild).  
   Alternative: separate analytics floor config — rejected (one floor keeps eval and diagnostics aligned).

2. **Empty filtered window fails rebuild**  
   If no draws remain after the floor, `build-analytics` errors naming `min_contest` (same spirit as evaluation load checks). No silent empty profiles.

3. **Experiment column `min_contest` (nullable INTEGER)**  
   Add via `ALTER TABLE` when missing. `NULL` means no floor was configured at compare time (or legacy row). Also include `min_contest` inside `policy_evidence` JSON for evidence completeness.  
   Alternative: evidence-only — rejected; column is easier to list/filter.

4. **List output**  
   `list-experiments` includes the floor when present (compact: `min_contest=2088` or omit/null).

5. **Operator rebuild**  
   After changing `min_contest`, operators must re-run `build-analytics` so show-* match the new window.

## Risks / Trade-offs

- **[Risk] Stale analytics after config change** → Mitigation: document rebuild; optional one-line contest range on build output.
- **[Risk] Legacy experiments lack column** → Mitigation: nullable; readers treat null as unknown.
- **[Trade-off] Full-history analytics unavailable while floor is set** → Accept; omit/null floor and rebuild to restore full-history diagnostics.

## Migration Plan

1. Schema migrate experiments DB on open; ship CLI/analytics wiring.
2. Operator: `build-analytics` under current floor; new compares store `min_contest`.
3. Rollback: set `min_contest` null, rebuild analytics, continue (new experiments store null).

## Open Questions

- Whether show-* should refuse to run if analytics DB contest metadata disagrees with current config (lean: no in v1; trust rebuild discipline).
