# PLAN: SampleOrderSystem

## 1. Purpose of This Document

This is a **high-level phased roadmap**, not the granular TDD implementation
plan. Each phase below still goes through this project's established
process before any code is written: brainstorming → design spec
(`docs/superpowers/specs/`) → detailed implementation plan
(`docs/superpowers/plans/`) → execution via
`superpowers:subagent-driven-development`. This document exists to answer
one question first: **in what order do we tackle SampleOrderSystem's
pieces, and why** — so each phase's brainstorming starts with the right
scope instead of re-deciding sequencing every time.

See `PRD.md` for what's being built and `CLAUDE.md` for curriculum context
and conventions already established across the 4 PoC stages.

## 2. Guiding Principles

- **Reuse over rewrite.** Each PoC proved a pattern in isolation; adapt
  that pattern here rather than redesigning it. Where a PoC's pattern
  doesn't fit the real requirements (e.g. `ConsoleMVC`'s PoC used
  user-entered ids; the PRD's decisions log says ids are now
  system-assigned), adapt deliberately and note the deviation — don't
  silently diverge.
- **One phase at a time.** Finish and manually verify one phase before
  starting the next; later phases depend on earlier ones being real and
  working, not stubbed.
- **Business logic lives here, not in the PoCs.** None of the 4 PoCs
  implement order-status transitions, stock math, or production
  scheduling — that's this repo's entire reason to exist. Don't try to
  backport business logic into the PoC repos; build it fresh here,
  informed by what they proved about structure.
- **Every phase ends working end-to-end**, not just unit-tested — a
  manual console smoke test is part of each phase's definition of done,
  same as every PoC stage.

## 3. Target Package Structure

Adapting `ConsoleMVC`'s layout (proven structure) with `DataPersistence`'s
persistence pattern (proven storage) and real business logic layered in:

```
SampleOrderSystem-yulgon-09013121/
  main.py
  model/
    sample.py            # Sample dataclass (real fields, see PRD §5.1)
    order.py              # Order dataclass + OrderStatus (real fields, see PRD §5.2)
    production_queue.py   # ProductionQueueEntry — one shortfall, FIFO queue state
  persistence/
    repository.py         # JsonRepository (adapted from DataPersistence, real ids)
    sample_repository.py  # typed wrapper: Sample <-> dict via JsonRepository("samples")
    order_repository.py   # typed wrapper: Order <-> dict via JsonRepository("orders")
  view/
    console_view.py       # ConsoleView (adapted from ConsoleMVC)
  controller/
    app_controller.py         # status bar + main menu dispatch
    sample_controller.py      # 시료 관리
    order_controller.py       # 시료 주문 + 승인/거절 (business logic: stock check, routing)
    monitor_controller.py     # 모니터링 (adapts DataMonitor's read/refresh pattern to real queries)
    production_controller.py # 생산 라인 (FIFO queue, production math, completion)
    release_controller.py    # 출고 처리
  data/                    # real runtime JSON files (gitignored, same convention as the 4 PoCs)
```

Exact file boundaries may shift once each phase is actually brainstormed —
this is a target, not a contract.

## 4. Phased Roadmap

### Phase 1 — Foundation: Model + Persistence

**Goal:** real `Sample`/`Order` dataclasses and a working persistence layer
underneath them, with system-assigned sequential ids (PRD §5.1/5.2,
decisions log #4).

**Reuses:** `DataPersistence`'s `JsonRepository` (`max+1` id scheme,
`create`/`get`/`list_all`/`update`/`delete`), adapted directly (this repo
can share code with itself, unlike the separate PoC repos).

**Deliverables:** `model/sample.py`, `model/order.py`, `persistence/`
(generic repository + typed sample/order wrappers), with real CRUD
verified by tests — no console UI yet.

**Definition of done:** can create/read/update/delete samples and orders
via Python calls (no menu yet), backed by real JSON files, with tests
covering the id scheme and typed conversion.

### Phase 2 — Sample Management Menu (시료 관리)

**Goal:** real 시료 등록/조회/검색 (PRD §6.1), replacing ConsoleMVC's
echo-only stub with real persistence-backed behavior.

**Reuses:** `ConsoleMVC`'s `ConsoleView`/menu-loop pattern; Phase 1's
sample repository.

**Definition of done:** can register, list, and search real samples from
the console, persisted across restarts.

### Phase 3 — Order Intake (시료 주문)

**Goal:** real 시료 예약 (PRD §6.2) — order manager records an order
against an existing sample id, status `RESERVED`, real persistence.

**Reuses:** Phase 1's order repository; `ConsoleMVC`'s order-controller
shape (adapted from echo-only to real).

**Definition of done:** can reserve an order referencing a real existing
sample, persisted with status `RESERVED`.

### Phase 4 — Approve/Reject Business Logic (주문 승인/거절)

**Goal:** the core business decision (PRD §6.3): approve routes to
`CONFIRMED` (sufficient stock, stock deducted) or `PRODUCING` (insufficient
stock, shortfall registered — see Phase 5); reject routes to `REJECTED`.

**New logic (not in any PoC):** stock-sufficiency check, stock deduction,
status routing. This is this phase's actual engineering content — no PoC
modeled it.

**Definition of done:** approving/rejecting a real `RESERVED` order
produces the correct status and stock effects per PRD §6.3, verified by
tests covering both branches (sufficient/insufficient stock) plus reject.

**Depends on:** Phase 5's queue existing (at least as a data structure) so
"insufficient stock" has somewhere real to register the shortfall — these
two phases may need to be sequenced or brainstormed together depending on
how tightly coupled the queue's interface ends up being.

### Phase 5 — Production Line (생산 라인)

**Goal:** the FIFO shortfall queue and production math (PRD §6.6): each
shortfall its own queue entry, `ceil(부족분/수율)` actual production
quantity, `평균생산시간 × 실생산량` total time, completion adds the
shortfall to stock and flips the order `PRODUCING` → `CONFIRMED`.

**New logic (not in any PoC):** the queue itself, the production math, and
—the one thing not yet decided anywhere — **how "production completes" is
triggered** in a console app with no background scheduler (a manual
"advance"/"complete next" menu action vs. simulated elapsed time vs.
something else). This must be resolved during this phase's brainstorming,
not assumed here.

**Definition of done:** 생산 현황 and 대기 주문 확인 (PRD §6.6's exact
field list) display correctly, math matches the formulas exactly, and
completing production correctly updates stock and order status.

### Phase 6 — Release Processing (출고 처리)

**Goal:** real 출고 처리 (PRD §6.5) — a `CONFIRMED` order transitions to
`RELEASE`.

**Definition of done:** releasing a real `CONFIRMED` order updates its
status; attempting to release a non-`CONFIRMED` order is rejected.

### Phase 7 — Monitoring (모니터링)

**Goal:** real 주문량 확인 / 재고량 확인 (PRD §6.4) — status-grouped order
counts (REJECTED excluded) and per-sample stock level
(여유/부족/고갈 per the decisions-log thresholds).

**Reuses:** `DataMonitor`'s read/refresh-on-demand pattern, adapted from
"dump raw JSON" to "compute real aggregates from the repositories."

**Definition of done:** monitoring screens show correct live aggregates
that update after any prior phase's actions (approve, release, produce,
etc.), refreshed on demand.

### Phase 8 — Status Bar + Final Wiring

**Goal:** wire the status bar (PRD §6.0) to real aggregate counts, and
assemble `main.py` end-to-end across every controller built in Phases 2-7.

**Definition of done:** the full menu (0-7 per PRD §6) works end-to-end
from a cold start with an empty `data/` directory through registering
samples, taking orders, approving/rejecting, producing, releasing, and
monitoring — a full manual smoke test walking every path once.

### Phase 9 — Seeding & Manual End-to-End Verification

**Goal:** use `DummyDataGenerator`'s pattern (not necessarily the PoC repo
directly, since ids must match Phase 1's real scheme) to seed realistic
sample/order data, then manually exercise the full system against it.

**Definition of done:** a populated system (multiple samples, multiple
orders in various statuses) behaves correctly across every menu, and
`DataMonitor`'s pattern could point at this repo's real `data/` directory
without modification (per PRD §7's non-functional requirement).

## 5. Sequencing Rationale

Phases 1-3 are strictly sequential (model → persistence → UI needs both).
Phase 4 and 5 are tightly coupled (approval needs somewhere to register a
shortfall; the queue needs approval to be the thing that populates it) —
flagged above as possibly needing a combined brainstorming session rather
than two fully separate ones. Phases 6-8 are each independent once 1-5
exist, but are listed in an order that lets manual smoke-testing
accumulate incrementally (release needs confirmed orders to exist;
monitoring is most useful once there's varied state to observe). Phase 9
is last because it depends on everything else being real.

## 6. Open Design Question Carried Into Phase 5

Unlike the PRD's decisions log (already resolved), one design question is
deliberately **not** pre-decided here: how production completion is
triggered without a background scheduler. Options to weigh when Phase 5 is
brainstormed include a manual "생산 완료 처리" menu action, an elapsed
wall-clock check against 예상완료, or a "advance simulation" command. This
is called out explicitly so it isn't silently assumed mid-implementation.

## 7. Next Step

Brainstorm Phase 1 (`superpowers:brainstorming`) to produce its design spec
and implementation plan, then execute via
`superpowers:subagent-driven-development`, same process as all 4 PoC
stages.
