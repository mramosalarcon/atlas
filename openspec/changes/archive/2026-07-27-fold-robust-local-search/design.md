## Context

Current local search maximizes aggregate train primary (≥3 hits) then coverage. That produced a strong modern-window champion that still dominates freeze folds. Holdout-favored hybrids beat the last 15% but fail 0/5 folds. Operators want a search objective aligned with walk-forward stability so a new candidate can legitimately challenge the champion under unchanged freeze policy and `min_contest`.

## Goals / Non-Goals

**Goals:**

- Fold-robust hill climb: partition the **provided train draws** with the same contiguous fold logic freeze uses (`n_folds` from config).
- Lexicographic train objective: `(min_fold_primary, sum_fold_primary, total_primary, pairs, triples, quads)`.
- Covering seed + same legal single-number replacement neighborhood as local search.
- CLI `optimize-fold-robust` exporting a non-predictive comparison candidate.
- Config knobs under `optimizer.fold_robust`.

**Non-Goals:**

- Changing freeze thresholds, bootstrap, or tournament accept rules.
- Reading validation/holdout during optimize.
- Replacing or removing existing local-search / greedy / covering / ensemble.
- Guaranteeing tournament promotion (success = runnable candidate + fold-aware search; promotion is empirical).

## Decisions

1. **New strategy class, reuse move machinery**  
   Add `FoldRobustOptimizer` (e.g. `atlas/optimization/fold_robust.py`) that seeds via `CoveringOptimizer` and hill-climbs with a fold-aware score. Reuse `apply_replacement` / neighborhood patterns from local search rather than forking ticket validation.  
   Alternative: replace local-search objective in place — rejected (breaks current champion reproducibility and removes a useful baseline).

2. **Fold partition source**  
   Call `partition_contiguous_folds(train_draws, n_folds)` with `evaluation.freeze_policy.n_folds`. CLI passes `n_folds` into optimize (via settings or explicit arg on the strategy).  
   Alternative: hardcode 5 — rejected (must track config).

3. **Objective definition**  
   For system `S` on train draws:  
   - `fold_i = primary_metric(S, fold_i_draws)`  
   - score = `(min(fold_i), sum(fold_i), primary(S, all train), pairs, triples, quads)` lexicographic max.  
   This approximates “don’t sacrifice early modern folds for late-window gains” without peeking at holdout.  
   Alternative: maximize fold-pass count vs a frozen baseline during search — rejected for v1 (couples search to champion file; harder to test).

4. **Config shape**  
   ```yaml
   optimizer:
     fold_robust:
       enabled: true
       max_passes: 20
       primary_metric_min_hits: 3
   ```  
   Defaults mirror local-search where sensible. Require `max_passes >= 1` and `primary_metric_min_hits` in a valid hit range consistent with other optimizers.

5. **CLI**  
   `atlas optimize-fold-robust --output … [--compare-baseline …]` mirroring other optimize commands: load evaluation draws (honors `min_contest`), split train/validation, optimize on train only, optional freeze compare.

6. **Reporting**  
   Report seed, train contest range, fold count, final `(min_fold, sum_fold, total_primary)`, coverage counts, and non-predictive banner. Optionally list per-fold train primaries for operator insight.

## Risks / Trade-offs

- **[Risk] Still loses to aggregate local-search** → Mitigation: smoke compare; if weak, follow-up may seed from local-search or raise pass budget—not in v1 scope.
- **[Risk] Slower than aggregate local-search** (score recomputes per fold) → Mitigation: keep incremental hit matrix if easy; otherwise accept slower optimize for clarity in v1.
- **[Risk] Overfitting to train fold boundaries** → Mitigation: same partition as freeze; no holdout in search; freeze remains the accept gate.
- **[Trade-off] Objective ≠ freeze delta vs champion** → Accept; train robustness is a proxy, tournament decides.

## Migration Plan

1. Ship config + strategy + CLI + tests.
2. Operator: `optimize-fold-robust` → `run-tournament` (or `--compare-baseline` vs current champion).
3. Rollback: disable `optimizer.fold_robust.enabled` / stop using the CLI; existing optimizers unchanged.

## Open Questions

- Whether a later variant should seed from current champion JSON (lean: no in v1).
- Whether report should always dump per-fold train metrics (lean: yes, compact one line per fold).
