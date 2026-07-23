## Context

ATLAS Core already compares systems on one chronological validation slice (`validation_ratio`) and accepts if `delta >= min_absolute_delta`. Analytics and greedy optimizer now generate candidates that can pass a lucky single window. The PRD’s evidence policy called for walk-forward / stronger significance; this change upgrades the freeze rule without changing how optimizers search.

## Goals / Non-Goals

**Goals:**

- Walk-forward folds over contest-ordered history for baseline vs candidate.
- Accept only when a configured fraction (or count) of folds each meet `min_absolute_delta` improvement on the primary metric.
- Optional paired bootstrap gate on deltas (seeded, reproducible).
- Persist and display the evidence used for the decision.
- Backward-compatible config defaults that are stricter than today’s single-window rule.

**Non-Goals:**

- Changing the primary metric itself (still counts of draws with best hits ≥ K).
- Auto-tuning fold count from data mining.
- Bayesian models, multiple-testing correction across many candidates (document as future).
- Optimizer changes.

## Decisions

1. **Walk-forward folding scheme**  
   Sort draws by `CONCURSO`. Split into `n_folds` contiguous segments of (nearly) equal size. For fold `i` (1..n_folds), the **test segment** is fold `i`; comparison metrics for the freeze policy are computed on each test segment independently (expanding-train is optional later). v1 uses **contiguous partition folds** (simpler, fast, enough to stop single-window luck).

2. **Accept rule (v1 default)**  
   Accept iff:
   - `passes >= required_fold_passes` where a fold “passes” when `candidate_metric - baseline_metric >= min_absolute_delta` on that fold’s test segment, **and**
   - if `bootstrap.enabled`: lower bound of the paired bootstrap CI for mean fold-delta is `>= bootstrap.min_ci_lower` (default `0`).

3. **Keep single-window summary for UX**  
   Still compute and store the classic last-`validation_ratio` window metrics as a labeled diagnostic (`holdout_metric`), but **decision** follows walk-forward (+ bootstrap), not the holdout alone.

4. **Bootstrap method**  
   When enabled: resample fold deltas with replacement (`n_resamples`, `seed`), compute percentile CI (`ci_level`, default 0.95). Paired at fold level (same folds for both systems).

5. **Config under `evaluation.freeze_policy`** (or top-level `freeze_policy`)  
   Suggested:
   ```yaml
   evaluation:
     validation_ratio: 0.15          # retained for holdout diagnostic + optimizer train split
     min_absolute_delta: 1
     primary_metric_min_hits: 3
     freeze_policy:
       n_folds: 5
       required_fold_passes: 4
       bootstrap:
         enabled: false
         n_resamples: 1000
         ci_level: 0.95
         seed: 42
         min_ci_lower: 0
   ```

6. **Experiment store**  
   Add a JSON `policy_evidence` column (or extend payload) with fold rows and bootstrap summary; keep existing columns populated (holdout window + overall decision) for compatibility.

7. **Policy version string**  
   Stamp experiments with `freeze_policy_version: "walkforward-v1"` so old vs new decisions are auditable.

## Risks / Trade-offs

- **[Risk] Stricter policy rejects almost everything** → Mitigation: configurable folds/required passes; start with defaults that are stricter but attainable; document tuning.
- **[Risk] Contiguous folds correlate** → Mitigation: still better than one window; expanding walk-forward can be a later version.
- **[Risk] Schema migration for experiments DB** → Mitigation: additive column; rebuild-safe or `ALTER TABLE` on open.
- **[Trade-off] Bootstrap off by default** → Faster MVP path; enable in config when desired.

## Migration Plan

1. Add config + settings.
2. Implement fold splitter + freeze decision function.
3. Wire `compare_systems` to new policy; extend experiment persistence.
4. Update CLI output and tests (accept/reject fixtures for multi-fold).
5. No change to raw history DB.

## Open Questions

- Whether `required_fold_passes` should be a ratio (`0.8`) instead of absolute count (absolute is clearer in logs).
- Whether holdout `validation_ratio` window should remain required in reports or become optional.
