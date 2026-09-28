## 1. Config

- [x] 1.1 Add `cover_orders` and `order_weights` defaults to `optimizer.covering` in `config/config.yaml` (include 2 and 3; optional 4 off by default)
- [x] 1.2 Extend covering settings + loader validation (orders ⊆ {2,3,4}, require 2, positive weights for each enabled order)
- [x] 1.3 Add config tests for defaults and invalid multi-order covering settings

## 2. Multi-order covering

- [x] 2.1 Add k-tuple helpers (enumerate tuples in a number set; coverage union for k=2,3,4)
- [x] 2.2 Build per-order uncovered weight maps from train draws (`train_frequency` / `uniform`) scaled by `order_weights`
- [x] 2.3 Generalize ticket construction: seed from best uncovered tuple; grow by max newly covered effective weight across orders
- [x] 2.4 Remove all fully covered k-tuples after each completed ticket
- [x] 2.5 Update covering unit tests for triples, determinism, and order-2-required behavior
- [x] 2.6 Extend covering optimize report with pair/triple/quad coverage counts (non-predictive)

## 3. Local search alignment

- [x] 3.1 Extend local-search objective to `(primary, pairs, triples, quads)` with deterministic acceptance
- [x] 3.2 Update local-search report and unit tests for higher-order tie-breaks

## 4. Smoke

- [x] 4.1 Smoke `optimize-covering` (and `optimize-local` if touched) vs current champion; confirm pytest passes
