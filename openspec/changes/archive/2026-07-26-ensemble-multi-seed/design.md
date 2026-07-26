## Context

ATLAS has greedy, covering, and local-search optimizers plus a ladder tournament. Each optimize run yields one system for one seed. Operators already keep multiple exports (`greedy_*`, `covering_*`, `local_search_*`). This change formalizes pooling those tickets (from multi-seed runs and/or files) and drafting a single valid 8-ticket challenger judged only by freeze policy.

## Goals / Non-Goals

**Goals:**

- Deterministic ensemble: pool unique tickets from multi-seed strategy runs and/or JSON systems; draft `system_size` tickets.
- Train-only search/draft scoring (same draw set contract as other strategies).
- Config + CLI parity (`optimize-ensemble`, optional compare-baseline).
- Non-predictive candidate reporting.

**Non-Goals:**

- Genetic algorithms or learned ticket weights.
- Changing freeze policy or tournament semantics.
- Guaranteeing a better champion.
- Auto-entering ensemble into every tournament without an export file.

## Decisions

1. **Two input modes**  
   - **Generate:** for each seed in `optimizer.ensemble.seeds`, run each listed source strategy (`greedy`, `covering`; local-search optional/deferred if too slow) on the provided draws with that seed injected into settings.  
   - **Files:** load tickets from explicit system JSON paths (`--sources`).  
   Modes may combine (union of tickets).

2. **Draft algorithm**  
   Start with empty selection. While `|selected| < system_size`, add the unused pooled ticket that maximizes train objective `(primary_metric_count, pair_coverage)` of the partial system; ties broken by ascending ticket number tuple.  
   If the pool has fewer than `system_size` unique tickets, fail clearly.  
   Alternative considered: random draft — rejected for determinism.

3. **Seed injection**  
   For generate mode, construct `OptimizerSettings` copies with `seed` replaced per ensemble seed (greedy uses seed; covering largely lex-deterministic but still records seed; do not require local-search in v1 by default because of runtime).

4. **Config**  
   ```yaml
   optimizer:
     ensemble:
       enabled: true
       seeds: [42, 7, 99, 123, 256]
       sources: [greedy, covering]  # strategy names
   ```
   Shared `primary_metric_min_hits` comes from evaluation via local_search pattern or evaluation at CLI time.

5. **Package / CLI**  
   `atlas/optimization/ensemble.py` implementing `OptimizationStrategy` for generate mode; file-mode drafting as a function used by CLI.  
   `atlas optimize-ensemble --output ... [--sources FILE ...] [--compare-baseline ...]`.

6. **Dedup**  
   Tickets identified by sorted number tuples; pool is a set.

## Risks / Trade-offs

- **[Risk] Pool dominated by near-duplicate covering tickets** → Mitigation: multi-seed greedy adds diversity; file mode can mix hand systems.
- **[Risk] Generate mode slow (many covering+greedy runs)** → Mitigation: default seeds short; file mode for fast drafts; local-search not in default sources.
- **[Risk] Train-metric draft overfits** → Mitigation: freeze policy (+ bootstrap) still gates promotion.
- **[Trade-off] No local-search in default sources** → Keep v1 fast; allow adding later via config.

## Migration Plan

1. Config + settings/loader for ensemble.
2. Pool + draft + `EnsembleOptimizer` + tests.
3. CLI + smoke vs champion / tournament export.
4. No DB schema changes.

## Open Questions

- Whether to include `local_search` in default `sources` after timing smoke.
- Whether draft should prefer pair coverage alone for speed (deferred; use primary+pairs for consistency with local-search).
