## 1. Config

- [x] 1.1 Add optional `tournament` section to `config/config.yaml` (champion path, roster_glob)
- [x] 1.2 Extend typed settings + loader so missing `tournament` remains valid; expose defaults when present
- [x] 1.3 Add config tests for absent vs present tournament defaults

## 2. Ladder runner

- [x] 2.1 Implement roster resolution (explicit paths and/or glob; exclude champion; stable order)
- [x] 2.2 Implement ladder loop: compare each challenger vs current champion via existing freeze-policy compare
- [x] 2.3 Promote champion only on `accepted`; keep champion on `rejected`
- [x] 2.4 Build tournament summary (id, schedule, duel outcomes, final champion) with non-predictive banner
- [x] 2.5 Optional JSON export of the summary when an output path is provided
- [x] 2.6 Add unit tests for promotion, rejection retention, and duel count = challenger count

## 3. CLI and smoke

- [x] 3.1 Add `run-tournament` CLI (`--champion`, challengers and/or roster glob, `--output`)
- [x] 3.2 Smoke with real exports (e.g. local_search vs covering/greedy/mikelito); confirm pytest passes
