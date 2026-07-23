## 1. Config

- [x] 1.1 Add `optimizer` section to `config/config.yaml` (`seed`, `candidate_pool_size`, greedy enabled flag)
- [x] 1.2 Extend typed settings + loader with `require_optimizer`; fail clearly if optimize is requested without the section
- [x] 1.3 Add config tests for optimizer defaults and missing-section error

## 2. Strategy interface and pair helpers

- [x] 2.1 Define `OptimizationStrategy` protocol/ABC returning a valid `TicketSystem`
- [x] 2.2 Implement unordered pair helpers (pairs in a ticket; coverage union; new-pair count)
- [x] 2.3 Add unit tests for pair counting and incremental new-pair scoring

## 3. Greedy optimizer

- [x] 3.1 Implement seeded candidate ticket generation bounded by `candidate_pool_size`
- [x] 3.2 Implement greedy construction: pick tickets by max new pair coverage with deterministic tie-break until `system_size`
- [x] 3.3 Add tests for deterministic reproduction (same seed → same system) and incremental coverage behavior
- [x] 3.4 Format optimize summary text as comparison-candidate only (non-predictive language)

## 4. CLI and smoke

- [x] 4.1 Add `optimize-greedy` CLI: split train/validation, optimize on train only, write system JSON export
- [x] 4.2 Optionally support comparing the exported candidate to a baseline via existing compare flow (or document one-liner)
- [x] 4.3 Smoke on Melate history: produce a system, evaluate/compare safely; confirm pytest passes
