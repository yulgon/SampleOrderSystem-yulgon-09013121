# Phase 4 — Approve/Reject Business Logic — Design

## Context

This is Phase 4 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phase 3 built 시료 예약 (`OrderController.run_reserve()`). This phase adds
the core business decision from PRD §6.3: approving a `RESERVED` order
routes it to `CONFIRMED` (stock deducted immediately) if stock covers it,
or to `PRODUCING` (a shortfall is registered) if it doesn't; rejecting
routes it to `REJECTED`.

PLAN.md flagged Phase 4 and Phase 5 (생산 라인) as tightly coupled, since
"insufficient stock" needs somewhere real to register the shortfall. This
phase's scope was explicitly narrowed with the user: Phase 4 creates the
shortfall record (a `ProductionQueueEntry`, with its intrinsic values —
actual production quantity, total production time — computed at creation
time, since those don't depend on queue position). Phase 5 owns everything
about *processing* that queue: FIFO ordering, starting/completing
production, the 생산 현황/대기 주문 확인 screens, and the still-open
question of how production completion is triggered (see `PLAN.md` §6).

## Scope

**In scope:** `OrderController.run_approve_reject()` — 접수된 주문 목록 (list
`RESERVED` orders), 주문 승인 (approve: stock-sufficient → deduct stock,
`CONFIRMED`; stock-insufficient → create a `ProductionQueueEntry`,
`PRODUCING`), 주문 거절 (reject → `REJECTED`). A new `ProductionQueueEntry`
model and `ProductionQueueRepository` (create/list_all only — no
update/delete yet, since nothing in this phase mutates an entry after
creation).

**Out of scope:** any FIFO processing, production-start/completion
logic, the 생산 현황/대기 주문 확인 display screens (all Phase 5). Stock is
NOT deducted on the insufficient-stock path in this phase — per PRD §6.6,
that happens when production completes (Phase 5).

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  model/
    production_queue_entry.py       # ProductionQueueEntry dataclass
  persistence/
    production_queue_repository.py   # ProductionQueueRepository: create(), list_all()
  controller/
    order_controller.py (modified)   # adds run_approve_reject() to the existing class
```

## `ProductionQueueEntry`

Fields: `entry_id` (system-assigned, same max+1 scheme as everything
else), `order_id`, `sample_id`, `shortfall`, `actual_qty`, `total_time`.

- `actual_qty = ceil(shortfall / sample.yield_rate)` — computed at creation
  time (doesn't depend on queue position).
- `total_time = sample.avg_production_time * actual_qty` — likewise
  computed at creation time.
- Minimal `__post_init__` validation: `shortfall > 0`, `actual_qty > 0`,
  `total_time > 0` (defensive; these should always hold given the caller
  only creates an entry when stock is actually insufficient).

`ProductionQueueRepository` follows the exact same wrapper pattern as
`SampleRepository`/`OrderRepository`: strips any pre-existing id before
`create()`, validates before any write it were to support `update()` (not
needed yet since no `update()` method exists in this phase).

## Menu Flow

```
주문 (승인/거절): 1. 접수된 주문 목록   2. 주문 승인   3. 주문 거절   4. 돌아가기

1 -> list orders with status RESERVED; "접수된 주문이 없습니다." if none
2 -> loop: prompt 주문 ID -> look up via OrderRepository.get()
        if not found OR status != RESERVED: "유효한 접수 주문이 아닙니다." and
        re-prompt the SAME field
     -> look up the order's Sample via SampleRepository.get()
     -> if sample.stock >= order.qty:
          SampleRepository.update(sample_id, {"stock": stock - qty})
          OrderRepository.update(order_id, {"status": CONFIRMED})
          show "승인 완료 (재고 차감): ..."
        else:
          shortfall = qty - stock
          actual_qty = ceil(shortfall / yield_rate)
          total_time = avg_production_time * actual_qty
          ProductionQueueRepository.create(ProductionQueueEntry(...))
          OrderRepository.update(order_id, {"status": PRODUCING})
          show "재고 부족 - 생산 등록: 부족분=..., 실생산량=..., 총생산시간=..."
3 -> loop: prompt 주문 ID -> same not-found/not-RESERVED validation as
        approve -> OrderRepository.update(order_id, {"status": REJECTED})
        -> show confirmation
4 -> return
```

## Error Handling

Same retry-until-valid convention as Phases 2-3: an order id that doesn't
exist or isn't `RESERVED` shows an error and re-prompts the SAME field —
never bounces back to the 승인/거절 submenu mid-operation. Invalid submenu
choice: "잘못된 입력입니다.", re-show the submenu.

## Testing

`ProductionQueueEntry`/`ProductionQueueRepository` tested the same way as
`Sample`/`SampleRepository` (unit + `tmp_path`-backed integration).
`OrderController.run_approve_reject()` tested with `FakeView` plus real
`SampleRepository`/`OrderRepository`/`ProductionQueueRepository` (all
`tmp_path`): list with/without pending orders; approve with sufficient
stock (verify stock deducted, order `CONFIRMED`); approve with
insufficient stock (verify a `ProductionQueueEntry` was created with the
correct computed values, order `PRODUCING`, stock unchanged); reject
(verify `REJECTED`); invalid/not-RESERVED order id retry.

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-4-approve-reject`, merged via a PR the
user reviews and merges manually.
