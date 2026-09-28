## Why

Pair-only covering was an intentional v1 limit; Melate tickets are 6-number sets, so hit patterns of 3+ and 4+ depend on triple/quad coverage that the current heuristic never targets. With ensemble and local-search already competing on pairs + primary metric, richer covering (and matching local-search scoring) is the next lever for stronger freeze-policy challengers.

## What Changes

- Extend the covering optimizer to construct tickets against uncovered **pairs, triples, and optionally quads**, with configurable cover orders and relative weights.
- Extend covering config (`optimizer.covering`) for cover orders / higher-order weights; reject invalid settings clearly.
- Optionally enrich local-search objective tie-breaks with triple (and quad) coverage so polish aligns with the richer covering signal.
- Keep train-only search, deterministic construction, and non-predictive CLI reporting; freeze policy remains the only accept path.
- Export path remains `optimize-covering` (and local-search if objective changes); no new mandatory CLI unless reporting needs a flag.

## Capabilities

### New Capabilities

- _(none — extend existing covering / config / local-search capabilities)_

### Modified Capabilities

- `covering-optimizer`: Requirements change from pair-only construction to multi-order (pair/triple/quad) covering with deterministic tie-breaks.
- `config-manager`: Load and validate covering higher-order settings (orders + weights).
- `local-search-optimizer`: Objective / reporting may include triple (and optional quad) coverage as additional deterministic tie-break after primary metric and pair coverage.

## Impact

- `atlas/optimization/covering.py`, `atlas/optimization/pairs.py` (or new tuples helpers), `atlas/optimization/local_search.py`
- `atlas/config/settings.py`, `atlas/config/loader.py`, `config/config.yaml`
- `atlas/cli.py` covering/local-search reports
- Tests: covering, config, local-search; smoke vs current champion
- Tournament/ensemble unchanged unless covering export improves and is re-entered manually
