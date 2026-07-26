## Context

Pairwise `compare-systems` already applies walk-forward freeze policy and logs experiments. Operators currently script ladders by hand (`covering` vs `local_search`, etc.). This change adds a thin orchestration layer: schedule challengers against a sticky champion, reuse `compare_systems` for every duel, and summarize outcomes. Freeze policy remains the only accept/reject authority.

## Goals / Non-Goals

**Goals:**

- Ladder tournament: champion + ordered challenger roster of system JSON files.
- Each challenger faces the **current** champion once; on `accepted`, challenger becomes champion for remaining matches.
- Tournament summary (stdout + optional JSON) listing duel decisions and final champion path/name.
- CLI `run-tournament` composing existing load/compare/store paths.
- Optional YAML defaults for champion and roster glob.
- Non-predictive copy in reports (historical comparison only).

**Non-Goals:**

- Round-robin, Swiss, or knockout brackets.
- Calling optimizers mid-tournament (roster is frozen exports only).
- Changing freeze-policy thresholds or primary metric.
- Dashboard / Streamlit.
- New experiment DB schema beyond tagging tournament id in the report (experiments stay as today).

## Decisions

1. **Mode = ladder only (v1)**  
   Sticky champion matches the “no adoption without freeze accept” rule and avoids non-transitive ranking debates.  
   Alternative: round-robin — deferred; better as a later research mode.

2. **Promotion semantics**  
   After each duel, if decision is `accepted`, set `champion = challenger` for subsequent duels in the same run. If `rejected`, champion unchanged.  
   Challenger order is CLI-specified (or sorted paths when using a directory/glob) so runs are reproducible.

3. **Composition over new arbiter**  
   Every duel calls existing `compare_systems(baseline=champion, candidate=challenger, ...)`. Holdout diagnostics remain diagnostic; fold evidence stays on each experiment record.

4. **Roster input**  
   CLI: `--champion PATH` required (or from config default); `--challengers PATH [PATH ...]` and/or `--roster-glob` (e.g. `data/exports/*_candidate.json`). Exclude the champion path from the challenger list if it appears in the glob.  
   Systems are loaded with existing JSON loader rules.

5. **Tournament identity**  
   Generate a `tournament_id` (UTC timestamp slug) for the run. Include it in the summary JSON and printed header. Do **not** require a new SQLite table in v1; experiment rows remain pairwise. Optional: put `tournament_id` in stdout so operators can correlate with `list-experiments` timestamps.

6. **Config**  
   ```yaml
   tournament:
     champion: data/exports/local_search_candidate.json  # optional default
     roster_glob: data/exports/*_candidate.json          # optional
   ```
   Absent `tournament` section is fine; CLI flags required then.

7. **Package**  
   `atlas/tournament/ladder.py` (run + summary types) + CLI wiring. Keep evaluation package free of CLI concerns.

## Risks / Trade-offs

- **[Risk] Challenge order changes final champion** → Mitigation: document order; print schedule before running; stable sort when using globs.
- **[Risk] Operators treat tournament winner as predictive** → Mitigation: non-predictive banner; same freeze language as compare.
- **[Risk] Glob pulls sample/junk JSON** → Mitigation: exclude `sample_*` by default or document; allow explicit path lists.
- **[Trade-off] No round-robin** → Ladder first; matrix later if needed.

## Migration Plan

1. Config optional section + loader.
2. Ladder runner + unit tests (fake compare or small fixtures).
3. CLI + smoke with 2–3 exports against current champion.
4. No raw history DB changes.

## Open Questions

- Whether summary JSON should optionally copy the winning system to a fixed `data/exports/champion.json` path (deferred; operators can `cp` after accept).
- Default exclude patterns for roster globs (`sample_*`, `*_uniform.json`).
