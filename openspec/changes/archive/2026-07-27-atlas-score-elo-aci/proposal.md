## Why

Operators can accept/reject challengers and run a sticky ladder, but there is still no stable, comparable **ranking signal** across many systems and historical duels—only binary decisions and raw holdout deltas. Atlas Score, Elo rating, and ACI intervals were deferred from core MVP and analytics; with tournament + bootstrap in place, this is the right moment to add historical ranking without changing the promotion gate.

## What Changes

- Introduce **Atlas Score**: a deterministic composite score for an 8-ticket system on a provided draw set (historical evaluation only; not a prediction).
- Introduce **Atlas Rating (Elo)**: ratings updated from logged freeze-policy duel outcomes (and optionally from tournament summaries), persisted and reportable.
- Introduce **ACI (Atlas Confidence Interval)**: bootstrap confidence intervals around Atlas Score (and optionally around score deltas between two systems).
- Add config for scoring weights, Elo knobs (initial rating, K), and ACI resample settings (may reuse evaluation bootstrap knobs where appropriate).
- Add CLI to score systems, show ratings, and report ACI—always with non-predictive banners.
- Freeze-policy accept/reject and tournament promotion remain unchanged; Score/Elo/ACI MUST NOT auto-promote champions.

## Capabilities

### New Capabilities

- `atlas-score`: Compute and report a composite historical score for a ticket system on a provided draw set.
- `atlas-rating`: Maintain and update Elo-style ratings from freeze-policy duel results.
- `aci-intervals`: Bootstrap Atlas Confidence Intervals around Atlas Score (and pairwise score deltas).

### Modified Capabilities

- `config-manager`: Load scoring / rating / ACI settings from YAML.
- `strategy-comparison`: Optionally attach Atlas Score / ACI diagnostics to comparison reports without changing decision logic.
- `strategy-tournament`: Optionally update and summarize Elo ratings after a ladder run without changing promotion rules.

## Impact

- New package (e.g. `atlas/scoring/` or `atlas/rating/`) plus CLI subcommands
- `config/config.yaml`, settings, loader
- Optional hooks in comparison/tournament report formatters
- Experiment store may gain a ratings table or sidecar JSON under `data/processed/`
- Tests for score determinism, Elo updates, ACI bounds; smoke on current champion exports
- No change to freeze-policy accept criteria
