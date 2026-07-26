## Context

Covering is the freeze-policy champion. Regenerating covering after new draws, switching to `uniform` pair weights, and enlarging the greedy pool all failed to produce an `accepted` challenger against `covering_candidate.json`. ATLAS already has `OptimizationStrategy`, train-only search, and freeze-policy compare. This change adds a polish stage: start from covering’s constructive system, then apply small deterministic edits scored only on the provided (train) draws.

## Goals / Non-Goals

**Goals:**

- Third optimizer: local search seeded from covering (default) that returns a valid 8-ticket system.
- Deterministic results for fixed draws, rules, seed, and local-search settings.
- Train-only objective aligned with the freeze primary metric (count of draws where best ticket has ≥ `primary_metric_min_hits`), with pair-coverage as a tie-break.
- Config + CLI parity (`optimize-local`, optional `--compare-baseline`).
- Non-predictive reporting; accept/reject only via existing freeze policy.

**Non-Goals:**

- Genetic algorithms, simulated annealing temperature schedules, or population methods.
- Tournament/league CLI.
- Changing freeze-policy thresholds or fold logic.
- Reading validation/holdout draws inside the strategy.
- Guaranteeing a better champion (search may return the seed unchanged).

## Decisions

1. **Seed**  
   Default: run `CoveringOptimizer` on the same draws/settings (respecting `covering.pair_weight`), then polish.  
   Alternative considered: seed from greedy — rejected as default because covering is the current champion; optional later via config if needed.  
   v1: covering seed only (no CLI seed-file) to keep scope tight.

2. **Neighborhood**  
   Single-ticket number replacement: for ticket `t`, replace one main number `a` with `b` not already on `t`, producing a valid ticket under rules; system must keep 8 distinct ticket number-sets (reject duplicates).  
   Alternative considered: cross-ticket swaps only — weaker diversity.  
   Alternative considered: unrestricted random mutations — less deterministic / harder to test.

3. **Search order & acceptance**  
   First-improvement hill-climb: enumerate candidate moves in lexicographic order `(ticket_index, removed_number, added_number)`; accept the first move that strictly improves the train objective; restart enumeration after each accept until a full pass finds no improvement or `max_passes` is reached.  
   Tie-break when primary metric equal: accept only if system unordered pair-coverage increases.  
   Use `optimizer.seed` only if a residual randomized break is ever needed; v1 prefers pure lex order (seed recorded in report for parity with other optimizers).

4. **Train objective**  
   Primary: number of draws in the provided set where the system’s best ticket has ≥ `evaluation.primary_metric_min_hits` main hits (same definition freeze uses per fold).  
   Strategy receives `min_hits` via optimizer settings or an explicit argument from CLI loaded from config — do **not** import validation draws.  
   Alternative considered: optimize pair coverage only — already near-saturated by covering; unlikely to move freeze outcomes.

5. **Config**  
   ```yaml
   optimizer:
     local_search:
       enabled: true
       max_passes: 20
   ```
   Reuse shared `seed`. Covering settings still apply for the seed construction.

6. **Package / CLI**  
   `atlas/optimization/local_search.py` implementing `OptimizationStrategy`.  
   CLI `optimize-local` mirrors greedy/covering (split train/validation outside strategy, export JSON, optional compare).

## Risks / Trade-offs

- **[Risk] Train-metric hill-climb overfits early contests / fails freeze** → Mitigation: still judged only by walk-forward vs champion; no auto-promote.
- **[Risk] Neighborhood too small to escape covering local optimum** → Mitigation: document; follow-up can add 2-swap or multi-start seeds.
- **[Risk] Expensive if naively rescoring all draws per candidate move** → Mitigation: incremental best-hit updates or cache per-draw best hits; keep `max_passes` bounded.
- **[Trade-off] First-improvement vs best-improvement** → First-improvement is faster and still deterministic given lex order.

## Migration Plan

1. Config + settings/loader for `local_search`.
2. Implement strategy + unit tests (seed unchanged when no improving move; determinism; move validity).
3. CLI + smoke: `optimize-local --compare-baseline data/exports/covering_candidate.json`.
4. No raw DB schema changes.

## Open Questions

- Whether to expose `seed_strategy: covering|greedy` in v1 (deferred; covering only).
- Whether `max_passes` default of 20 is enough on Melate history (tune after smoke).
