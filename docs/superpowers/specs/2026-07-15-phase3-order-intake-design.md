# Phase 3 — Order Intake — Design

## Context

This is Phase 3 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phase 1 built `Sample`/`Order` + persistence; Phase 2 built the 시료 관리
menu. This phase builds 시료 예약 (order reservation) per PRD.md §6.2 — the
order manager records a customer's desired sample and quantity, referencing
an *existing* sample, persisted with status `RESERVED`. Approval/rejection
(PRD §6.3) is explicitly **not** in scope here — that's Phase 4, added to
the same `OrderController` class later.

## Scope

**In scope:** `OrderController.run_reserve()` — collects an existing
`sample_id`, `customer`, `qty`; creates an `Order` with status `RESERVED`
via `OrderRepository`. A small temporary main menu (0/1/2) replacing Phase
2's single-controller `main.py`, letting a manual tester reach both 시료
관리 and 시료 주문 in one run.

**Out of scope:** 주문 승인/거절 (Phase 4), any stock deduction or
production-queue interaction (Phase 4+), a real `AppController` (Phase 8).

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  main.py                      # temporary menu: 0 종료 / 1 시료 관리 / 2 시료 주문
  controller/
    order_controller.py         # OrderController.run_reserve() only (Phase 4 adds run_approve_reject to the same class)
```

## Flow

```
run_reserve():
  loop: prompt 시료 ID -> SampleRepository.get(id)
        if None: show "존재하지 않는 시료 ID입니다." and re-prompt the SAME field
        else: break with the found sample
  prompt 고객명 (no validation, same treatment as Phase 2's sample name)
  loop: prompt 주문 수량 -> parse int -> Order's own qty>0 rule
        on parse failure or qty<=0: re-prompt the SAME field
  OrderRepository.create(Order(sample_id=..., customer=..., qty=..., status=RESERVED))
  show confirmation with the assigned order_id
```

`main.py`'s temporary menu:

```
0. 종료   1. 시료 관리   2. 시료 주문
1 -> SampleController(view).run()
2 -> OrderController(view).run_reserve()
0 -> exit
invalid -> "잘못된 입력입니다.", re-show
```

This inline loop lives directly in `main.py` (not a separate class) since
it's explicitly temporary — Phase 8 replaces it with a real
`AppController`.

## Error Handling

Same retry-until-valid convention as Phase 2: invalid 시료 ID (not found)
or invalid 주문 수량 (non-numeric or non-positive) re-prompt the same
field, never bouncing back to a higher menu mid-reservation. Invalid main
menu choice: "잘못된 입력입니다.", re-show the menu.

## Testing

`OrderController.run_reserve()` tested with `FakeView` plus real
`SampleRepository`/`OrderRepository` (both over `tmp_path`): a sample is
registered first (setup), then reservation is exercised for the
happy path, the not-found-sample-id retry, and the invalid-qty retry.
`main.py`'s temporary menu is verified only by manual smoke test (same
convention as Phase 2), not automated — its content is explicitly
throwaway.

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-3-order-intake`, merged via a PR the
user reviews and merges manually.
