## Context

Core MVP provides import, evaluation, train/validation split, and freeze-policy comparison. Analytics v1 provides diagnostics. `atlas/optimization/` is empty. This change adds the first optimizer behind a plugin interface so later algorithms compete under the same contract.

Non-negotiable: search uses **train draws only**; promotion uses existing validation compare + experiment log.

## Goals / Non-Goals

**Goals:**

- Define `OptimizationStrategy` with a single optimize entrypoint returning a valid `TicketSystem`.
- Implement deterministic greedy construction of `system_size` tickets.
- Drive greedy steps primarily by **new unordered pair coverage** across tickets (combinatorial objective valid under randomness).
- Report train primary metric (`hits_at_least_3`) as a diagnostic after construction.
- Config-driven seed and candidate-search limits; CLI export + optional baseline compare.

**Non-Goals:**

- Genetic algorithm, simulated annealing, Monte Carlo, tournament, ensemble.
- Changing freeze-policy thresholds or primary metric definition.
- Using validation/test draws inside the optimizer.
- Claiming the greedy output predicts future draws.

## Decisions

1. **Plugin interface first**  
   `OptimizationStrategy.optimize(draws, rules, settings) -> TicketSystem` (name configurable). Callers depend on the interface, not greedy specifics.

2. **Train-only input**  
   CLI/optimizer entry loads history, splits with existing `split_train_validation`, passes **train** only into `optimize`. Validation is used only if the user runs compare afterward.

3. **Greedy objective: maximize incremental pair coverage**  
   Maintain the set of unordered pairs covered by tickets already chosen. For each new ticket slot, evaluate candidate tickets and pick the one adding the most new pairs. Ties broken deterministically (e.g. lexicographic ticket numbers, then candidate order).

4. **Candidate generation is seeded and bounded**  
   Generate up to `candidate_pool_size` distinct valid tickets per slot via seeded RNG (or deterministic enumeration of a bounded sample). Config defaults chosen for speed on ~4k train subset (actually train is ~85% of 4k). No OR-Tools.

5. **Partial systems during search**  
   Pair coverage works on 1..system_size tickets without requiring a full system for the greedy step. Final output MUST still be a full `TicketSystem` validated by rules.

6. **Post-build diagnostic**  
   After building, optionally evaluate the full system on train and print primary metric / coverage—clearly labeled diagnostic. Accept/reject remains `compare-systems`.

7. **Config shape**  
   ```yaml
   optimizer:
     seed: 42
     candidate_pool_size: 500
     greedy:
       enabled: true
   ```
   Missing `optimizer` section fails clearly when optimize CLI is invoked (`require_optimizer`).

8. **Package layout**  
   `atlas/optimization/strategy.py`, `atlas/optimization/greedy.py`, `atlas/optimization/pairs.py` (pair helpers), wire CLI in `atlas/cli.py`.

## Risks / Trade-offs

- **[Risk] Overfitting if greedy maximized train hit counts** → Mitigation: primary greedy step uses pair coverage, not hit maximization.
- **[Risk] Weak candidates from small pool** → Mitigation: configurable `candidate_pool_size`; document that larger pools improve search, not validation honesty.
- **[Risk] Users treat optimizer output as “the answer”** → Mitigation: CLI banner states candidate for comparison only; does not predict draws.
- **[Trade-off] Greedy ≠ global optimum** → Acceptable; it is the intentional baseline algorithm.

## Migration Plan

1. Add config + settings/loader helpers.
2. Implement pair helpers + greedy + strategy interface.
3. Unit tests with tiny number ranges / fixtures.
4. CLI `optimize-greedy` writing JSON under `data/exports/`.
5. Smoke: optimize on Melate train → compare to sample baseline → experiment logged.

## Open Questions

- Whether to add a second greedy mode (`hits` vs `pairs`) behind a config flag later (default pairs only in this change).
- Default export path naming (`greedy_<seed>.json` vs timestamp).
