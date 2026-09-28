## ADDED Requirements

### Requirement: Covering cover orders and order weights are loaded from config
The system SHALL load covering `cover_orders` and per-order relative weights from YAML config and expose them to the covering optimizer, and MUST NOT hardcode those values inside the covering strategy.

#### Scenario: Default cover orders and weights present
- **WHEN** `config/config.yaml` defines `optimizer.covering.cover_orders` and `optimizer.covering.order_weights`
- **THEN** the loaded config exposes those values to the covering optimizer

### Requirement: Invalid covering multi-order settings fail clearly
The system SHALL fail configuration load with a clear error if `cover_orders` is empty, contains a value outside `{2, 3, 4}`, omits `2`, or if `order_weights` is missing a required order or has a non-positive weight.

#### Scenario: Cover orders omit pairs
- **WHEN** config sets `cover_orders` without `2`
- **THEN** configuration load raises an error stating order 2 is required

#### Scenario: Unsupported cover order
- **WHEN** config lists a cover order other than 2, 3, or 4
- **THEN** configuration load raises an error naming the invalid order
