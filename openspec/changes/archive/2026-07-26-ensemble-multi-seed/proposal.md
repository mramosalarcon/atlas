## Why

Single-seed greedy, covering, and local-search each produce one 8-ticket system. Diversity from multiple seeds (and multiple strategies) is left on the table unless operators hand-merge exports. An **ensemble multi-seed draft** pools tickets from several train-only runs, then drafts a valid 8-ticket system to challenge the champion under freeze policy—cheap diversity before heavier algorithms.

## What Changes

- Add an ensemble path that runs configured strategies across a list of seeds on the train window only, pools unique tickets, and drafts exactly `system_size` tickets into one `TicketSystem`.
- Support drafting from existing system JSON files as an alternate input (no re-optimize) for fast tournament challengers.
- Add `optimizer.ensemble` config (enabled, seeds, source strategies, draft objective knobs).
- Add CLI `optimize-ensemble` (export JSON + optional `--compare-baseline` / tournament-ready output).
- Keep freeze policy as the only accept gate; non-predictive reporting.
- Out of scope: genetic ensembles, stacking models, changing freeze rules, mid-tournament re-optimize, dashboard.

## Capabilities

### New Capabilities
- `ensemble-optimizer`: Multi-seed / multi-source ticket pooling and deterministic draft into an 8-ticket comparison candidate.

### Modified Capabilities
- `config-manager`: Load `optimizer.ensemble` settings; reject invalid seeds/strategy lists.
- `optimization-strategy`: Clarify that ensemble may invoke multiple strategies and seeds while staying on the provided draw set.

## Impact

- New module under `atlas/optimization/` (e.g. `ensemble.py`) plus config/CLI/tests.
- Reuses greedy/covering (and optionally local-search) as ticket sources; reuses train scoring helpers where useful.
- Tournament can treat the ensemble export as another challenger JSON.
