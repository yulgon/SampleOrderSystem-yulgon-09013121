# PRD: SampleOrderSystem

## 1. Overview

SampleOrderSystem is a console-based (number-input, menu-driven) Python
program for managing sample ("시료") orders and production. It is used
directly by two internal roles — an order manager and a production
manager — to record customer sample requests, approve or reject them,
track production, and release finished orders.

This is the final, real (non-PoC) stage of a 5-stage learning curriculum.
Stages 1-4 each proved out one structural concern in isolation, with no
real business logic:

| Stage | What it proved | Reused here as |
|---|---|---|
| ConsoleMVC | Model/View/Controller package separation for the console UI | The UI package structure (`model/`, `view/`, `controller/`) |
| DataPersistence | Generic JSON-file CRUD (`JsonRepository`, max+1 sequential ids) | The persistence layer for samples/orders |
| DataMonitor | Read-only, refresh-on-demand console viewer over stored JSON | The 모니터링 menu's underlying read pattern |
| DummyDataGenerator | Random test-data generation referencing existing records | A seeding tool for manual testing (not part of the shipped app) |

SampleOrderSystem is where these patterns get wired together **and** where
the real business logic they all deliberately omitted — order status
transitions, stock accounting, production scheduling — finally gets built.

The authoritative domain source is `../description.md` (workspace root).
This PRD restates and organizes that content; if anything here conflicts
with `description.md`, treat `description.md` as authoritative and flag the
discrepancy.

## 2. Goals

- Let an order manager record customer sample requests as orders.
- Let a production manager register new sample types, and approve or
  reject incoming orders.
- Automatically route approved orders either straight to fulfillment
  (sufficient stock) or into a production queue (insufficient stock).
- Give both roles a real-time view of order volume and stock health.
- Support releasing (shipping) orders once their stock is ready.
- Model a single-line production process that manufactures only what's
  been ordered, accounting for yield loss.

## 3. Non-Goals

- No GUI or web interface — console only, menu-number input.
- No multi-user/concurrent access handling — single operator at a time
  (matches the JSON-file persistence layer's single-process assumption
  carried over from DataPersistence).
- No customer-facing interface — customers interact only via email,
  outside the system; the order manager is the one who enters requests.
- No authentication/authorization — anyone running the console can act as
  either role.
- No multiple production lines — exactly one production line, producing
  one sample type at a time (see §6.6).

## 4. Users / Roles

| Role | Description | Responsibilities in-system |
|---|---|---|
| 고객 (Customer) | External; not a system user | Requests desired samples by email (outside the system) |
| 주문 담당자 (Order manager) | Internal | Enters orders based on customer requests (시료 주문 메뉴) |
| 생산 담당자 (Production manager) | Internal | Registers new sample types, approves/rejects orders, manages production and release |

The system does not distinguish these roles at login — both operate the
same console, choosing whichever menu their task requires.

## 5. Domain Model

### 5.1 Sample (시료)

| Field | Description |
|---|---|
| `sample_id` | System-assigned sequential integer (max existing id + 1), same scheme as `DataPersistence`'s `JsonRepository` — the user never enters this |
| `name` | 시료명 |
| `avg_production_time` | 평균 생산시간 (used to compute total production time) |
| `yield_rate` | 수율 — fraction of production output that is usable (0.9 = 90% of produced units are good). Formula: `수율 = 정상 생산 수량 / 총 생산 수량` |
| `stock` | 현재 재고 (current on-hand quantity) |

### 5.2 Order (주문)

| Field | Description |
|---|---|
| `order_id` | System-assigned sequential integer (max existing id + 1), same scheme as `sample_id` |
| `sample_id` | The sample being ordered (user selects an existing `sample_id`, doesn't invent one) |
| `customer` | 고객명 |
| `qty` | 주문 수량 |
| `status` | One of the 5 statuses below |

### 5.3 Order Status Lifecycle

```
RESERVED --(reject)--> REJECTED
RESERVED --(approve, stock sufficient)--> CONFIRMED
RESERVED --(approve, stock insufficient)--> PRODUCING --(production completes)--> CONFIRMED
CONFIRMED --(release)--> RELEASE
```

| Status | Meaning |
|---|---|
| `RESERVED` | 주문 접수 — newly placed, awaiting approval/rejection |
| `REJECTED` | 주문 거절 — terminal; excluded from active monitoring counts |
| `PRODUCING` | 승인 완료, 재고 부족으로 생산 중 — queued/running in the production line |
| `CONFIRMED` | 승인 완료, 출고 대기 중 — stock is sufficient (either originally or after production), ready to release |
| `RELEASE` | 출고 완료 — terminal; order fulfilled |

## 6. Functional Requirements (by menu)

### 6.0 Status Bar (always visible above the main menu)

Displays, refreshed on every menu redraw:
- 등록시료 (count of registered sample types)
- 총 재고 (sum of stock across all samples)
- 전체주문 (count of all orders — see §6.4 for which statuses count)
- 대기중인 생산라인 (count of orders currently `PRODUCING` / queued)

### 6.1 시료 관리 (Sample Management)

- **시료 등록 (Register):** create a new `Sample` — collects `name`,
  `avg_production_time`, `yield_rate`, `stock`; `sample_id` is
  system-assigned (see §5.1).
- **시료 조회 (List):** show every registered sample, including current
  stock.
- **시료 검색 (Search):** find a sample by name (or other attributes).

### 6.2 시료 주문 (Sample Ordering)

- **시료 예약 (Reserve):** the order manager records a customer's desired
  sample and quantity. Collects, in order: `sample_id` (of an existing
  sample), `customer`, `qty`. `order_id` is system-assigned (see §5.2). The
  new order is created with status `RESERVED`.

### 6.3 주문 (승인/거절) (Order Approve/Reject)

- **접수된 주문 목록 (List pending):** show all `RESERVED` orders.
- **주문 승인 (Approve):** for a selected `RESERVED` order —
  - If `sample.stock >= order.qty`: deduct the stock, set status to
    `CONFIRMED` immediately.
  - If `sample.stock < order.qty`: register the shortfall with the
    production line (see §6.6) and set status to `PRODUCING`.
- **주문 거절 (Reject):** for a selected `RESERVED` order, set status to
  `REJECTED` immediately. No stock or production effects.

### 6.4 모니터링 (Monitoring)

- **주문량 확인 (Order volume):** counts of orders grouped by status —
  `RESERVED`, `CONFIRMED`, `PRODUCING`, `RELEASE`. **`REJECTED` orders are
  excluded** (not a "valid" order per `description.md`).
- **재고량 확인 (Stock levels):** per-sample current stock, compared
  against that sample's outstanding order demand (sum of `qty` across its
  `RESERVED` + `PRODUCING` orders):
  - 여유 (surplus) — `stock >= outstanding demand`
  - 부족 (shortage) — `0 < stock < outstanding demand`
  - 고갈 (depleted) — `stock == 0`

### 6.5 출고 처리 (Release)

- For a selected `CONFIRMED` order, execute release: set status to
  `RELEASE`. Only `CONFIRMED` orders are eligible.

### 6.6 생산 라인 (Production Line)

A single production line, producing one sample type at a time, only for
samples that have an actual order-driven shortfall. Each approved order
that lacked sufficient stock becomes its **own** queue entry — even if
another order for the *same* sample is already `PRODUCING` — and entries
are produced strictly one at a time in FIFO order (no merging of
same-sample shortfalls into a single production run).

- **생산 현황 (Current status):** for the entry currently in production,
  display: 순서 (its position when it started, or "현재 생산중"),
  주문번호 (order_id), 시료 (sample name), 주문량 (order qty), 부족분
  (shortfall), 실생산량 (actual production qty), 예상완료 (expected
  completion — start time + 총 생산 시간, or however time is tracked in
  this console context).
- **대기 주문 확인 (Pending queue):** the same field set (순서, 주문번호,
  시료, 주문량, 부족분, 실생산량, 예상완료) for every entry still waiting
  in the FIFO queue, in queue order.
- **Scheduling strategy:** FIFO — first shortfall queued is the first
  produced; the line processes one queue entry fully before starting the
  next, regardless of whether entries share a sample.
- **Production math**, applied when a shortfall enters production:
  - 실 생산량 (actual production quantity) = `ceil(부족분 / 수율)` — always
    rounded **up**, so production reliably covers the shortfall even after
    expected defect loss (e.g. shortfall 10, yield 0.9 → `ceil(11.11)` =
    12 produced).
  - 총 생산 시간 (total production time) = 평균 생산시간 (avg_production_time)
    × 실 생산량 (actual production quantity, the rounded-up value above).
  - On completion: add the shortfall quantity (not the rounded-up 실생산량
    — the excess above the shortfall accounts for defects and isn't extra
    usable stock beyond what was needed) to the sample's stock, and
    transition the associated order from `PRODUCING` to `CONFIRMED`.

## 7. Non-Functional Requirements

- **Persistence:** JSON files, one per collection (matching
  `DataPersistence`'s `JsonRepository` shape: `data/samples.json`,
  `data/orders.json`), so `DataMonitor`'s read pattern and
  `DummyDataGenerator`'s seeding both work against this system's real data
  path without modification.
- **UI:** console, numbered-menu navigation, Korean labels matching
  `description.md` exactly (this is user-facing text, not just internal
  naming).
- **Language/stack:** Python 3, pytest for tests — consistent with all 4
  PoC stages.
- **Process conventions** (carried over from the PoC stages, see this
  repo's `CLAUDE.md`): step-by-step implementation with a commit per step,
  English commit messages, work directly on `main` (no feature branches,
  confirmed per-repo with the user), brainstorming → spec → plan →
  subagent-driven execution for the implementation phase.

## 8. Success Criteria

- Every menu in §6 is implemented and reachable from the main menu.
- The 5-status order lifecycle (§5.3) and its transition rules (approve
  with/without sufficient stock, reject, release, production completion)
  are enforced exactly as specified — no status reachable via an
  unspecified path.
- Production math (실 생산량, 총 생산 시간) matches the formulas in §6.6
  exactly.
- Monitoring counts/labels match `description.md` exactly, including the
  `REJECTED`-excluded rule for order volume.
- Data persists across program restarts via the JSON persistence layer,
  and `DataMonitor` can read this system's real `data/` directory without
  changes.

## 9. Decisions Log

These were originally open gaps in `description.md`; each was resolved with
the user and folded into the relevant section above. Recorded here for
traceability:

1. **재고량 확인 thresholds** (§6.4): 여유 = `stock >= outstanding demand`,
   부족 = `0 < stock < outstanding demand`, 고갈 = `stock == 0`.
2. **생산 현황 display level** (§6.6): 순서, 주문번호, 시료, 주문량,
   부족분, 실생산량, 예상완료.
3. **Concurrent shortfalls for the same sample** (§6.6): each shortfall is
   its own FIFO queue entry, produced strictly one at a time — no merging
   of same-sample shortfalls.
4. **ID format** (§5.1, §5.2): `sample_id`/`order_id` are system-assigned
   sequential integers (max existing id + 1), matching `DataPersistence`'s
   `JsonRepository` scheme rather than `ConsoleMVC`'s PoC-era user-entered
   ID assumption.
5. **Rounding rule for 실생산량** (§6.6): always round up (`ceil`), so
   production conservatively covers the shortfall even after expected
   defect loss.

## 10. References

- `../description.md` — authoritative domain spec (workspace root)
- `CLAUDE.md` (this repo) — curriculum status and established conventions
- `../ConsoleMVC-yulgon-09013121/` — UI structure PoC
- `../DataPersistence-yulgon-09013121/` — persistence PoC
- `../DataMonitor-yulgon-09013121/` — monitoring PoC
- `../DummyDataGenerator-yulgon-09013121/` — test data generation PoC
