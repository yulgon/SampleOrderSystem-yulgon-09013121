# Phase 5 — Production Line — Design

## Context

This is Phase 5 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phase 4 built `ProductionQueueEntry`/`ProductionQueueRepository` (create +
list_all only) and started registering shortfalls when an order is
approved without sufficient stock. This phase builds the 생산 라인 menu
per PRD §6.6: FIFO queue display, and completing production (adding the
shortfall back to stock, flipping the order `PRODUCING` → `CONFIRMED`).

This phase also resolves `PLAN.md`'s open design question: **how
production completion is triggered.** Confirmed with the user: a manual
"생산 완료 처리" menu action completes whatever is currently at the head of
the FIFO queue, on demand — there is no background scheduler, no real
wall-clock tracking, and no automatic time-based completion. "예상완료" is
a **cumulative duration** (sum of `total_time` across the queue up to and
including the entry in question), not an absolute timestamp.

## Scope

**In scope:** `ProductionController` with 생산 현황 (head-of-queue detail),
대기 주문 확인 (full queue listing with cumulative expected-completion
duration), 생산 완료 처리 (complete the head entry: add its shortfall back
to stock, flip its order to `CONFIRMED`, remove it from the queue). Adding
`delete()` to `ProductionQueueRepository` (Phase 4 only had
create/list_all).

**Out of scope:** any wall-clock/timestamp tracking, automatic completion,
multiple simultaneous in-production entries (still exactly one at a time,
per PRD §6.6's single production line).

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  controller/
    production_controller.py   # 생산 라인 menu
  persistence/
    production_queue_repository.py (modified)  # adds delete()
```

## Queue Mechanics

No separate "in progress" vs. "waiting" status field is needed:
`ProductionQueueRepository.list_all()` already returns entries in
creation-id order, and since entries are only ever created (Phase 4, on
approval) or removed (this phase, on completion) — never reordered — the
first entry in that list IS the one currently being produced. Completing
it (`delete()`) makes the next entry (if any) the new head automatically.

"예상완료" for the Nth entry in the queue = sum of `total_time` for entries
1..N (itself included). The head entry's (N=1) expected-completion is just
its own `total_time`.

## Menu Flow

```
생산 라인: 1. 생산 현황   2. 대기 주문 확인   3. 생산 완료 처리   4. 돌아가기

1 -> if queue empty: "생산 중인 항목이 없습니다."
     else: show the head entry — 순서=1, 주문번호, 시료(via SampleRepository),
           주문량(via OrderRepository), 부족분, 실생산량, 예상완료(own total_time)
2 -> if queue empty: "대기 중인 생산이 없습니다."
     else: show every entry in queue order, 순서=1,2,3..., same field set,
           예상완료 = cumulative total_time up to and including that entry
3 -> if queue empty: "완료 처리할 생산이 없습니다."
     else: complete the head entry —
             SampleRepository.update(sample_id, {"stock": stock + shortfall})
             OrderRepository.update(order_id, {"status": CONFIRMED})
             ProductionQueueRepository.delete(entry_id)
           show a confirmation message
4 -> return
```

## Error Handling

No numeric input is collected in this controller (no id prompts) — every
action operates on the queue head or the full queue, so there's no
retry-until-valid loop needed here. Invalid main-submenu choice:
"잘못된 입력입니다.", re-show the submenu (existing convention).

## Testing

`ProductionQueueRepository.delete()` tested the same way as
`SampleRepository`/`OrderRepository`'s existing `delete()` methods
(`tmp_path`-backed). `ProductionController` tested with `FakeView` plus
real `SampleRepository`/`OrderRepository`/`ProductionQueueRepository` (all
`tmp_path`): empty-queue messages for all three actions; 생산 현황 and 대기
주문 확인 field display and cumulative-duration math with 2+ queued
entries; 생산 완료 처리's effects (stock increases by shortfall, order
becomes `CONFIRMED`, entry removed from queue) verified by reading back
via fresh repository instances; completing one entry correctly promotes
the next one to head-of-queue.

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-5-production-line`, merged via a PR
the user reviews and merges manually.
