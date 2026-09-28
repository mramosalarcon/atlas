## Context

ATLAS currently loads the full Melate raw history for optimize, compare, tournament, and scoring. Pool expansion means early contests under-represent balls 40–56 (52–56 appear near contest 2088/2089). Filtering the evaluation window via config avoids destructive CSV edits while aligning search and freeze policy with the modern game.

## Goals / Non-Goals

**Goals:**

- Configurable `evaluation.min_contest` (Melate default `2088`).
- All evaluation/optimize/compare/tournament/score draw loads honor the floor.
- Raw CSV import remains full-history; source CSV untouched.
- Clear errors when the filtered set is empty or insufficient for split/folds.

**Non-Goals:**

- Deleting or rewriting `Melate.csv`.
- Changing freeze fold counts or bootstrap knobs (except operating on fewer draws).
- Auto-promoting a new champion.
- Forcing analytics rebuild to use the same floor (keep full-history analytics unless explicitly wired later).

## Decisions

1. **Filter on load, not on import**  
   `import-history` continues to store all contests. A helper `load_draws_for_evaluation(config)` (or `load_draws(..., min_contest=...)`) returns contests with `contest >= min_contest`.  
   Alternative: truncate CSV — rejected (destructive, harder to reverse).

2. **Config field**  
   ```yaml
   evaluation:
     min_contest: 2088   # optional; omit or null = no floor (all contests)
   ```  
   Typed as `int | None`. Validation: if set, must be `>= 1`. Ship Melate default `2088`.

3. **Where the filter applies**  
   CLI/commands that evaluate or search strategies: `evaluate-system`, `compare-systems`, `optimize-*`, `run-tournament`, `score-system`, `score-aci`.  
   `import-history` and (v1) `build-analytics` / show-analytics keep full DB contents.

4. **Sufficiency checks**  
   After filter, require at least enough draws for train+validation (e.g. `n >= 2` and validation non-empty) and for freeze `n_folds` (each fold needs draws). Fail with a message naming `min_contest` and resulting count.

5. **Reporting**  
   Reports that mention contest ranges should reflect the filtered window (e.g. train contests start at ≥ 2088). Optional one-line note: `min_contest=2088 applied`.

6. **Champion continuity**  
   Document that re-running tournament after enabling the floor may crown a different champion; old full-history champion remains a file, not an automatic carry-over claim under the new window.

## Risks / Trade-offs

- **[Risk] Operators forget to regenerate candidates** → Mitigation: tasks/docs note regenerate + tournament after enabling.
- **[Risk] Analytics vs eval window mismatch** → Mitigation: leave analytics full; document; optional follow-up.
- **[Risk] Too-aggressive floor leaves few draws** → Mitigation: validate non-empty window; Melate 2088 still leaves ~2k draws.
- **[Trade-off] Champions not comparable across windows** → Accept; version experiments by config path / report contest range.

## Migration Plan

1. Config + settings/loader.
2. Shared filtered load helper; wire CLI/eval/compare paths.
3. Tests for filter and insufficient window.
4. Operator: regenerate optimizers + `run-tournament` under new window.
5. Rollback: set `min_contest` null/omit and reload.

## Open Questions

- Whether analytics should later honor the same floor (lean: no in v1).
- Whether experiment records should store `min_contest` explicitly (lean: yes if cheap via config_path + contest range already logged).
