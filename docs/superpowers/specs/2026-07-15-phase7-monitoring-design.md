# Phase 7 — Monitoring — Design

## Context

This is Phase 7 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phases 1-6 built the full order lifecycle (RESERVED → approve →
CONFIRMED/PRODUCING → [production] → CONFIRMED → RELEASE). This phase
builds 모니터링 per PRD §6.4: 주문량 확인 (order counts by status,
`REJECTED` excluded) and 재고량 확인 (per-sample stock vs. outstanding
demand, labeled 여유/부족/고갈 per the PRD decisions log).

Status bar (PRD §6.0) is explicitly out of scope here — `PLAN.md` assigns
it to Phase 8 alongside final `AppController` wiring.

## Scope

**In scope:** `MonitorController` with 주문량 확인 and 재고량 확인, computed
live from `SampleRepository`/`OrderRepository` — no new repository methods,
aggregation happens in the controller (same in-memory approach as
`SampleController`'s search).

**Out of scope:** the status bar, any real-time/DataMonitor-style refresh
loop beyond "recompute on each menu visit" (which is already how every
prior controller works — there's no caching anywhere in this codebase to
go stale).

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  controller/
    monitor_controller.py   # 모니터링 menu
```

## Menu Flow

```
모니터링: 1. 주문량 확인   2. 재고량 확인   3. 돌아가기

1 -> count OrderRepository.list_all() by status, for RESERVED/CONFIRMED/
     PRODUCING/RELEASE only (REJECTED excluded per PRD §6.4/decisions log)
     -> show each status's count (0 if none)
2 -> for each Sample in SampleRepository.list_all():
       outstanding_demand = sum(order.qty for order in orders
                                 if order.sample_id == sample.sample_id
                                 and order.status in {RESERVED, PRODUCING})
       if sample.stock >= outstanding_demand: label = "여유"
       elif sample.stock == 0: label = "고갈"
       else: label = "부족"        # 0 < stock < outstanding_demand
       show 시료명, 재고, label
     if no samples registered: "등록된 시료가 없습니다."
3 -> return
```

Note on label precedence: `stock == 0` always shows 고갈 even if
`outstanding_demand` is also 0 (no demand, zero stock) — 고갈 is a
statement about the stock quantity itself, not a comparison, matching the
PRD's literal definition ("수량이 0인 상태").

## Error Handling

Invalid submenu choice: "잘못된 입력입니다.", re-show the submenu (existing
convention). No numeric input prompts in this controller — both actions
are pure reports over existing data.

## Testing

`MonitorController` tested with `FakeView` plus real
`SampleRepository`/`OrderRepository` (`tmp_path`): 주문량 확인 with a mix of
statuses including `REJECTED` (confirm it's excluded) and with zero
orders; 재고량 확인 covering all three labels (여유/부족/고갈) including the
zero-stock-zero-demand edge case, and with zero samples registered.

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-7-monitoring`, merged via a PR the
user reviews and merges manually.
