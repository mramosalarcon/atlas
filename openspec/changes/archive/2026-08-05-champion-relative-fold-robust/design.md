## Context

Fold-robust currently maximizes absolute train fold primaries (`min_fold`, `sum_fold`, aggregate, coverage). Against the sticky local-search champion it tops out at 2/5 freeze-policy fold passes—even when seeded from the champion—because absolute strength ≠ per-fold delta vs baseline. Freeze policy on validation/holdout partitions uses `candidate_primary − baseline_primary` per fold with threshold `evaluation.min_absolute_delta`. This change aligns **train** search with that relative signal without changing freeze thresholds.

## Goals / Non-Goals

**Goals:**

- Optional objective mode `absolute` (current) vs `relative` (champion-relative).
- Relative mode: fix a baseline `TicketSystem`; score candidates by train fold deltas vs that baseline using the same contiguous `n_folds` partition and primary min-hits as fold-robust today.
- Lexicographic score for relative: `(fold_pass_count, sum_deltas, min_fold_primary, sum_fold_primary, aggregate_primary, pairs, triples, quads)` where a fold “passes” if `delta >= evaluation.min_absolute_delta`.
- Config + CLI to select mode and baseline path; report relative diagnostics.
- Keep absolute mode default for reproducibility of prior exports.

**Non-Goals:**

- Changing freeze policy, required fold passes, bootstrap, or tournament sticky rules.
- Searching on validation/holdout draws (train-only remains).
- Guaranteeing promotion.
- Soft Elo / auto ratings.
- Changing other optimizers’ objectives.

## Decisions

1. **Mode flag, not a separate optimizer**  
   `optimizer.fold_robust.objective: absolute | relative` (default `absolute`). Same neighborhood and seed_from behavior; only the score tuple changes.  
   Alternative: new `optimize-fold-relative` command — rejected; one CLI with a mode keeps operators on a single path.

2. **Baseline path for relative mode**  
   Resolve in order: CLI `--relative-to` → `optimizer.fold_robust.relative_to` → `optimizer.fold_robust.seed_from` → `tournament.champion`. Fail clearly if relative mode is on and no baseline file resolves.  
   Rationale: relative search without a baseline is undefined; chaining seed + relative-to the same champion is the common case.

3. **Precompute baseline fold primaries once**  
   On optimize start, partition train draws, compute baseline primary per fold, then for each candidate compute deltas as `cand[i] − base[i]`. Avoids reloading baseline tickets each move.

4. **Pass threshold from evaluation config**  
   Use `config.evaluation.min_absolute_delta` (same integer as freeze) for counting train fold “passes” in the objective. Do **not** duplicate a separate fold-robust threshold (avoids silent mismatch with the gate).

5. **Keep absolute components as lower tie-breakers**  
   After `(pass_count, sum_deltas)`, reuse absolute fold-robust / coverage keys so the hill climb still has a total order when relative keys tie.

6. **Report**  
   Include objective mode, baseline path/name, per-fold train deltas, and train fold-pass count. Non-predictive disclaimer unchanged.

7. **Shipped Melate default**  
   Leave `objective: absolute` in shipped YAML initially; document enabling `relative` + `relative_to` (or relying on seed_from/champion) for challenger runs. Optional: set `objective: relative` in shipped config only if smoke shows clear value—prefer operator opt-in in v1 to avoid surprise vs existing absolute exports.

## Risks / Trade-offs

- **[Risk] Train fold-pass count ≠ validation freeze fold-pass count** (different draw windows) → Mitigation: treat train relative score as a search heuristic; always `--compare-baseline` for the real gate; state this in report.
- **[Risk] Baseline == seed → early plateau / identity export** → Mitigation: expected; relative moves must beat the baseline on folds; more `max_passes` or different seed still allowed.
- **[Risk] Overfitting to train fold boundaries** → Mitigation: freeze + bootstrap unchanged; no holdout in search.
- **[Trade-off] Absolute vs relative candidates are not comparable by train report alone** → Accept; report mode explicitly; compare only via freeze policy.

## Migration Plan

1. Add settings/loader fields; implement relative score + hill climb branch; CLI flags; tests.
2. Operator: set `objective: relative` (or `--objective relative --relative-to <champion>`), export new candidate, `--compare-baseline` / tournament.
3. Rollback: `objective: absolute` restores prior behavior.

## Open Questions

- Whether shipped YAML should default `objective: relative` after first successful smoke (lean: keep absolute default; enable relative in smoke task only).
