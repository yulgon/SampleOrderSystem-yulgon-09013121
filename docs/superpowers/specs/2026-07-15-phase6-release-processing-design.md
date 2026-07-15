# Phase 6 — Release Processing — Design

## Context

This is Phase 6 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phases 1-5 built the full order lifecycle up through production
(`RESERVED` → approve → `CONFIRMED`/`PRODUCING` → complete production →
`CONFIRMED`). This phase adds 출고 처리 per PRD §6.5: a `CONFIRMED` order
transitions to `RELEASE`.

## Scope

**In scope:** a new `ReleaseController` (matching `ConsoleMVC`'s PoC
structure) with a single-action `run()`: prompt an order id, validate it
exists and is `CONFIRMED`, transition it to `RELEASE`.

**Out of scope:** everything else — this is the simplest remaining phase.

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  controller/
    release_controller.py   # ReleaseController.run()
```

## Flow

```
run():
  loop: prompt 주문 ID -> OrderRepository.get(id)
        if None or status != CONFIRMED:
          "출고 가능한(CONFIRMED) 주문이 아닙니다." and re-prompt the SAME field
  OrderRepository.update(order_id, {"status": RELEASE})
  show a confirmation message
```

Same retry-until-valid convention as Phases 3-4: never bounces to a higher
menu mid-operation.

## Error Handling

Non-numeric input, missing order, or an order that isn't `CONFIRMED` all
re-prompt the same 주문 ID field with an error message.

## Testing

`ReleaseController` tested with `FakeView` plus a real `OrderRepository`
(`tmp_path`): successful release (verify `CONFIRMED` → `RELEASE`); retry on
a non-existent order id; retry on an order that exists but isn't
`CONFIRMED` (e.g. still `RESERVED`).

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-6-release-processing`, merged via a
PR the user reviews and merges manually.
