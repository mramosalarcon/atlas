## Context

Greedy optimizer samples up to `candidate_pool_size` random tickets per slot and picks the one maximizing new pair coverage. That is a baseline. Covering design should construct tickets more deliberately from a pair-priority list derived from the train draw set (or uniform over all pairs in range). Freeze policy and strategy interface already exist.

## Goals / Non-Goals

**Goals:**

- Second `OptimizationStrategy` implementation: covering-design ticket construction.
- Deterministic results for fixed rules, draws, seed, and covering settings.
- Config + CLI parity with greedy (`optimize-covering`).
- Same non-predictive reporting and freeze-policy-only accept path.

**Non-Goals:**

- Optimal block designs / Schönheim bounds solvers.
- Triple/quad covering as the main loop (pairs only in v1).
- Tournament engine or automatic multi-algorithm league.
- Genetic algorithms.

## Decisions

1. **Pair priority source**  
   - `pair_weight: train_frequency` (default): rank unordered pairs by co-appearance count on the provided draw set (train), then by lex pair order.  
   - `pair_weight: uniform`: all pairs in `[min_number, max_number]` share equal weight; order by lex only.

2. **Ticket construction**  
   For each of `system_size` tickets:
   - Start with empty number set.
   - While `|numbers| < main_count`: choose the number that, if added, maximizes the total priority of pairs that would become newly covered (among pairs with both endpoints in the eventual ticket—use a constructive heuristic: score candidate numbers by sum of priorities of pairs `(n, x)` where `x` already in the ticket, plus pairs among future potential—**v1 simpler rule**):  
     **v1 algorithm:**  
     a. Take the highest-priority still-uncovered pair; seed the ticket with those two numbers (if ticket empty) or add the missing endpoint if exactly one is present and space remains.  
     b. Otherwise add the number that maximizes the sum of priorities of uncovered pairs connecting it to numbers already in the ticket.  
     c. Ties broken by smallest number, then by seed-stably shuffled residual only if needed (prefer pure numeric ties → full determinism without depending on pool size).

3. **After a ticket is completed**  
   Mark all its pairs as covered (remove from uncovered priority set). Proceed to next ticket.

4. **Shared settings**  
   Reuse `optimizer.seed` for any residual randomness; covering does **not** require `candidate_pool_size` (ignored). Config:
   ```yaml
   optimizer:
     seed: 42
     candidate_pool_size: 500  # greedy only
     greedy:
       enabled: true
     covering:
       enabled: true
       pair_weight: train_frequency  # or uniform
   ```

5. **CLI**  
   `optimize-covering --output ... [--compare-baseline ...]`: split train/validation, optimize on train, export, optional compare.

6. **Package**  
   `atlas/optimization/covering.py` implementing `OptimizationStrategy`.

## Risks / Trade-offs

- **[Risk] Heuristic covering ≠ optimal design** → Mitigation: treat as competitor candidate; freeze policy decides.
- **[Risk] train_frequency overweighting noisy pairs** → Mitigation: offer `uniform` mode; document both.
- **[Risk] Similar outputs to greedy** → Mitigation: construction path differs (pair-driven growth vs random pool); still valuable diversity.
- **[Trade-off] Pairs only** → Enough for second optimizer; triples later.

## Migration Plan

1. Config + settings for covering.
2. Implement covering strategy + tests (determinism, covers new pairs across tickets).
3. CLI + smoke vs greedy export under freeze policy.
4. No raw DB changes.

## Open Questions

- Whether to strip already-covered pairs from priority with soft weights instead of hard removal (hard removal in v1).
- Default `pair_weight` in shipped config (`train_frequency` recommended).
