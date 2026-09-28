## Context

ATLAS already evaluates systems, compares them under walk-forward + bootstrap freeze policy, logs experiments, and runs a sticky ladder tournament. What is missing is a durable **ranking layer**: a single-system historical score, a duel-derived Elo rating, and confidence intervals around scores. These were explicitly deferred from MVP and analytics-v1 as “Atlas Score / ELO / ACI”. Freeze policy remains the only promotion gate; ranking is diagnostic and comparative.

## Goals / Non-Goals

**Goals:**

- Deterministic **Atlas Score** for a system on a caller-provided draw set.
- **Atlas Rating (Elo)** updated from freeze-policy duel outcomes (`accepted` / `rejected`).
- **ACI**: bootstrap confidence interval around Atlas Score (and score delta for A vs B).
- Config + CLI + optional attachment to compare/tournament reports.
- Non-predictive wording everywhere; no auto-promotion from Score/Elo/ACI.

**Non-Goals:**

- Changing freeze-policy accept/reject rules.
- Dashboard / graphs UI (later).
- TrueSkill, Glicko, or Bayesian rating models.
- Using Score/Elo to regenerate tickets or auto-enter tournaments.
- Claiming predictive power for future Melate draws.

## Decisions

1. **Atlas Score formula (v1)**  
   On the provided draw set, compute components then a weighted sum (config weights, default shown):
   - `primary` = primary-metric count (`min_hits` from evaluation config) — weight `1.0`
   - `pairs` = unordered pair coverage count / scale — weight `0.01` (keeps magnitude near primary)
   - `triples` = triple coverage count / scale — weight `0.005`
   - Optional `quads` weight `0.0` by default (enable via config)  
   Scale factors: divide coverage counts by a constant (e.g. 100) or use raw counts with small weights—pick small weights on raw counts for simplicity.  
   Score is `sum(weight_i * component_i)`, rounded or left as float; report components alongside.  
   Alternative: PCA / learned weights — rejected for transparency and determinism.

2. **Draw set contract**  
   CLI defaults to the **validation/holdout window** for Score (comparable to holdout diagnostics) with a flag `--window {holdout,train,all}`. Core API always scores the draws passed in (same pattern as optimizers). Document that holdout Score is diagnostic only.

3. **Elo updates**  
   Classic Elo: expected score `E = 1 / (1 + 10^((Rb-Ra)/400))`; K from config (default 24); initial rating 1500.  
   Outcome for challenger vs champion baseline:
   - `accepted` → challenger score `1.0`, champion `0.0`
   - `rejected` → challenger `0.0`, champion `1.0`  
   Soft outcomes from fold-pass ratio deferred.  
   Identity key: system export stem / `TicketSystem.name` (stable string). Persist ratings in `data/processed/ratings.sqlite3` (or path from config).

4. **When Elo updates**  
   - Explicit CLI `update-ratings` from experiment log and/or  
   - Optional `--update-ratings` on `run-tournament` / after `compare-systems`  
   Default: tournament can update when flag set; compare stays opt-in to avoid surprise rating churn.

5. **ACI**  
   Resample **draws with replacement** (block or per-draw; v1: resample draw indices with replacement, same length), recompute Atlas Score each resample, report percentile CI at `ci_level` (default 0.95). Seed from config.  
   Pairwise ACI: bootstrap distribution of `score(candidate) - score(baseline)` on the same resampled indices.  
   Reuse bootstrap style from fold-delta CI but operate on scores, not fold deltas. Separate config under `scoring.aci` (n_resamples, ci_level, seed) rather than overloading freeze-policy bootstrap.

6. **Package / CLI**  
   - `atlas/scoring/score.py`, `elo.py`, `aci.py`, persistence helper  
   - CLI: `atlas score-system`, `atlas show-ratings`, `atlas score-aci` (names flexible); compare/tournament report hooks optional  
   - Reports MUST state historical / non-predictive / not a promotion decision

7. **Config sketch**
   ```yaml
   scoring:
     weights:
       primary: 1.0
       pairs: 0.01
       triples: 0.005
       quads: 0.0
     elo:
       initial_rating: 1500
       k_factor: 24
       ratings_db: data/processed/ratings.sqlite3
     aci:
       n_resamples: 1000
       ci_level: 0.95
       seed: 42
   ```

## Risks / Trade-offs

- **[Risk] Score weights feel arbitrary** → Mitigation: expose components; version the formula string in reports (`atlas-score-v1`).
- **[Risk] Elo from binary freeze outcomes is sparse/harsh** → Mitigation: document; K tunable; soft outcomes later.
- **[Risk] Operators confuse high Score with promote** → Mitigation: banners + specs forbid auto-promotion; freeze policy unchanged.
- **[Risk] ACI expensive on full history** → Mitigation: default holdout window; cap resamples in config.
- **[Trade-off] Holdout vs train for Score** → Default holdout for “how did it look on recent history”; train available via flag.

## Migration Plan

1. Config + settings/loader.
2. Score + unit tests.
3. ACI + tests.
4. Elo store + update + CLI.
5. Optional compare/tournament report attachments.
6. Smoke on champion + roster exports.

## Open Questions

- Whether default Elo updates should run automatically after every tournament (lean: opt-in flag).
- Whether quads should get a non-zero default weight after multi-order covering (lean: keep 0.0 until tuned).
