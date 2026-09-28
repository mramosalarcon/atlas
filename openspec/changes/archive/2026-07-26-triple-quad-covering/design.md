## Context

Covering v1 builds each ticket by greedily covering high-priority **unordered pairs**, then removes those pairs from an uncovered map. Local search polishes with objective `(primary_metric, pair_coverage)`. Pair-only search leaves triple/quad structure accidental. Melate mains are size 6, so 3- and 4-hit diagnostics align naturally with covering those subset sizes. Ensemble and tournament already exist for promotion; this change only strengthens the covering (and aligned local-search) candidates.

## Goals / Non-Goals

**Goals:**

- Multi-order covering: construct tickets against uncovered pairs, triples, and optionally quads.
- Config for `cover_orders` and per-order relative weights; reuse existing `pair_weight` mode (`train_frequency` | `uniform`) as the **tuple weight mode** for all orders.
- Deterministic, train-only construction; non-predictive reports that include higher-order coverage counts.
- Align local-search objective tie-breaks with triple (and optional quad) coverage after pairs.

**Non-Goals:**

- Exact optimal covering designs / Schönheim solvers / ILP.
- Changing freeze policy, tournament, or ensemble semantics.
- Guaranteeing a better champion.
- New optimizer CLI (keep `optimize-covering` / `optimize-local`).
- Covering orders above 4.

## Decisions

1. **Cover orders**  
   Config `optimizer.covering.cover_orders: [2, 3]` by default; allow `4` optionally. Must be a non-empty subset of `{2, 3, 4}` and must include `2` so pair behavior remains the baseline backbone (avoids empty-seed edge cases with only quads on sparse train).  
   Alternative: orders without requiring 2 — rejected for v1 seeding simplicity.

2. **Weight mode**  
   Keep YAML key `pair_weight` as the shared frequency mode for all k-tuples (rename in docs to “tuple weight mode”; no **BREAKING** key rename).  
   - `train_frequency`: weight(k-tuple) = count of draws whose mains contain that k-set.  
   - `uniform`: weight 1.0 for every valid k-tuple in range.  
   Relative scaling: `optimizer.covering.order_weights` map `{2: 1.0, 3: 1.0, 4: 0.5}` (defaults). Effective score uses `order_weights[k] * weight(tuple)`.

3. **Uncovered state**  
   Maintain one map per enabled order: `uncovered[k]: dict[tuple[int,...], float]`.  
   After each completed ticket, remove every k-tuple fully contained in the ticket’s numbers.  
   For `uniform` + order 4, materializing C(56,4)≈367k floats is acceptable for Melate-scale offline optimize; if smoke is slow, allow lazy uniform scoring (treat missing keys as 1.0) without storing all keys — prefer **eager maps for train_frequency**, **lazy unit weight for uniform** when `|universe|` would exceed a soft threshold (e.g. only store keys that appear while covering / score candidates on the fly). Implementer’s call with a comment; correctness over micro-opt.

4. **Ticket construction**  
   Generalize v1:
   - **Empty ticket:** seed with the highest-scoring still-uncovered tuple among enabled orders (score = effective weight); ties → prefer larger k, then lex tuple.
   - **Growth:** among candidates `n` not in the ticket, maximize sum over enabled k of effective weights of uncovered k-tuples that become fully contained in `ticket ∪ {n}` and were not fully contained before; ties → smallest `n`.
   - Repeat until `main_count` numbers; build `system_size` tickets.

5. **Local search**  
   Extend `objective_score` to  
   `(primary_metric_count, pair_coverage, triple_coverage, quad_coverage)`  
   where triple/quad counts are `|coverage_union_k(tickets)|` for k=3/4 (0 if that order disabled in covering config, or always compute if cheap). Prefer always computing 3 and 4 for polish consistency even if covering omitted 4.  
   Moves unchanged (single number swap); only acceptance uses richer lex order.  
   Alternative: reweight into a single scalar — rejected to keep determinism and explainability.

6. **Reporting**  
   Covering and local-search reports list covered pair/triple/quad counts (for enabled or always 2–4) and still state non-predictive / not auto-accepted.

7. **Package layout**  
   Add tuple helpers beside pairs (`tuples_in_numbers(k)`, `coverage_union_k`) in `pairs.py` or `tuples.py`; keep `CoveringOptimizer` in `covering.py`.

## Risks / Trade-offs

- **[Risk] Uniform quads memory/CPU** → Mitigation: lazy uniform scoring; default `cover_orders: [2, 3]` without 4.
- **[Risk] Higher-order train overfitting** → Mitigation: freeze policy (+ bootstrap) still gates promotion.
- **[Risk] Behavior change vs pair-only champion lineage** → Mitigation: defaults include pairs; document that covering exports will differ; re-run tournament manually.
- **[Trade-off] Require order 2** → Slightly less flexible; clearer seeding.

## Migration Plan

1. Config defaults + loader validation.
2. Tuple helpers + covering algorithm + tests.
3. Local-search objective + tests.
4. CLI report fields; smoke `optimize-covering` / `optimize-local` vs champion.
5. No DB migrations.

## Open Questions

- Whether default `cover_orders` should include `4` after timing smoke (start without; enable via config).
- Whether ensemble default sources should prefer new covering automatically (no — operator re-exports).
