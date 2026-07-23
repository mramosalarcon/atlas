## Why

The current freeze policy accepts a candidate when a single held-out validation window improves the primary metric by `min_absolute_delta`. That is easy to game with a lucky window and too weak for claiming a lasting strategy upgrade. A stronger freeze policy should require improvement across chronological walk-forward folds (and optionally a bootstrap confidence check) before accept.

## What Changes

- Replace single-window-only accept logic with a **walk-forward freeze policy**: evaluate baseline vs candidate on multiple chronological folds; accept only if enough folds improve by the configured absolute delta.
- Keep the existing primary metric (draws with best-ticket hits ≥ configured threshold) and `min_absolute_delta` as the per-fold floor.
- Optionally support a **paired bootstrap** of fold (or draw-level) deltas with a configured confidence level; when enabled, accept requires both walk-forward pass and bootstrap CI lower bound ≥ 0 (or ≥ delta).
- Persist richer experiment fields: fold metrics, pass counts, bootstrap summary when enabled, policy version.
- Extend `config.yaml` evaluation/freeze settings for fold count, required pass ratio, bootstrap toggles.
- Keep rejected experiments logged; do not change optimizer search behavior (train-only remains caller responsibility).
- Out of scope: changing primary metric definition to ROI, multi-objective Pareto accept, dashboard UI.

## Capabilities

### New Capabilities
- `walk-forward-evaluation`: Chronological multi-fold evaluation of baseline vs candidate with configurable fold count and pass criteria.
- `bootstrap-significance`: Optional paired bootstrap of metric deltas to support confidence-bounded accept/reject.

### Modified Capabilities
- `strategy-comparison`: Freeze policy accept/reject MUST use walk-forward (and optional bootstrap) instead of a single validation window alone; experiment records MUST store the richer evidence.
- `config-manager`: Add freeze-policy settings (folds, required passes, bootstrap enablement/params).

## Impact

- Updates `atlas/evaluation/comparison.py`, `split.py` (or new `walk_forward.py` / `bootstrap.py`).
- Extends experiment store schema carefully (additive columns or JSON payload field).
- Extends CLI compare output to show fold/bootstrap summary.
- Touches tests in `tests/test_comparison.py` and config tests.
- No new heavy dependencies (stdlib + existing stack).
