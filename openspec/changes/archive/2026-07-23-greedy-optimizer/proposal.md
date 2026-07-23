## Why

ATLAS can evaluate and compare 8-ticket systems and produce analytics diagnostics, but it cannot yet generate a candidate system automatically. A deterministic greedy optimizer closes that loop: propose a system on the train window, then accept or reject it only through the existing out-of-sample freeze policy.

## What Changes

- Introduce a common `OptimizationStrategy` interface so future algorithms (GA, annealing, covering) can plug in without changing callers.
- Implement a **Greedy** optimizer that builds an 8-ticket system using only the chronological **train** window.
- Prefer a coverage-oriented greedy step (maximize new main-number pair coverage when adding a ticket), with train primary-metric evaluation as a reported diagnostic—not as the accept/reject rule.
- Add config for optimizer parameters (seed, candidate pool size / search limits) under `config.yaml`.
- Add CLI to run greedy optimization, export the resulting system JSON, and optionally compare it to a baseline via the existing experiment log.
- Explicitly out of scope: genetic/annealing/monte-carlo/tournament/ensemble, auto-adopting winners without freeze policy, using validation data during search.

## Capabilities

### New Capabilities
- `optimization-strategy`: Shared optimizer interface and train-window-only contract for producing a `TicketSystem`.
- `greedy-optimizer`: Deterministic greedy construction of an 8-ticket system (pair-coverage greedy) with reproducible seeding.

### Modified Capabilities
- `config-manager`: Add optimizer/greedy settings (seed, search limits, output defaults) loaded from external config.

## Impact

- Fills `atlas/optimization/` (currently empty) with strategy interface + greedy implementation.
- Extends `atlas/config` and `config/config.yaml`.
- Adds CLI commands such as `optimize-greedy` (and optional compare wiring).
- Reuses `atlas/evaluation` (split, evaluate, compare) without changing freeze-policy semantics.
- No new heavy dependencies (stdlib + existing PyYAML/pytest).
