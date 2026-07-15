# Phase 8 — Status Bar + Final Wiring — Design

## Context

This is Phase 8 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phases 2-7 each added a temporary inline menu to `main.py` to make their
own controller manually testable, explicitly documented as throwaway.
This phase replaces that inline menu with a real `AppController` (matching
`ConsoleMVC`'s PoC pattern) with a live status bar (PRD §6.0), and makes
`main.py` itself minimal — just construction and `app.run()`.

Confirmed with the user: the real menu uses PRD §6's authoritative
numbering (1-7, exit=7) rather than the incremental numbering the
temporary per-phase menus happened to use (0=exit first, different
ordering) — those were always meant to be replaced, not preserved.

## Scope

**In scope:** `ConsoleView.show_status_bar(...)`, `AppController` (real
menu dispatch + live status bar), a minimal final `main.py`.

**Out of scope:** any new business logic — every status bar value is
computed by aggregating existing repositories, using the exact same
"REJECTED excluded" rule Phase 7's 전체주문 already established for order
counting.

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  view/
    console_view.py (modified)   # adds show_status_bar()
  controller/
    app_controller.py             # new: real menu dispatch + status bar
  main.py (rewritten)              # minimal: construct everything, app.run()
```

## `ConsoleView.show_status_bar`

```python
def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
    print(
        f"[상태] 등록시료: {registered_samples} | 총 재고: {total_stock} | "
        f"전체주문: {total_orders} | 대기중인 생산라인: {waiting_lines}"
    )
```

(Same format ConsoleMVC's PoC used, since it was never given real values
there.)

## `AppController`

```
MENU_OPTIONS = [
    (1, "시료 관리"), (2, "시료 주문"), (3, "주문 (승인/거절)"),
    (4, "모니터링"), (5, "출고 처리"), (6, "생산 라인"), (7, "종료"),
]
```

Each loop iteration, before showing the menu:
- 등록시료 = `len(SampleRepository.list_all())`
- 총재고 = `sum(s.stock for s in SampleRepository.list_all())`
- 전체주문 = count of orders with status != `REJECTED` (same rule as
  Phase 7's 전체주문/주문량 확인 view)
- 대기중인생산라인 = `len(ProductionQueueRepository.list_all())`

Dispatch: 1→`sample_controller.run`, 2→`order_controller.run_reserve`,
3→`order_controller.run_approve_reject`, 4→`monitor_controller.run`,
5→`release_controller.run`, 6→`production_controller.run`, 7→exit
message and return. Invalid choice: "잘못된 입력입니다.", re-show.

`AppController` builds its own `SampleRepository`/`OrderRepository`/
`ProductionQueueRepository` instances for the status bar computation
(same "each controller/component builds its own repositories" pattern
used everywhere else in this codebase — already confirmed safe/stateless
in earlier phases' reviews).

## `main.py` (final form)

```python
view = ConsoleView()
sample_controller = SampleController(view)
order_controller = OrderController(view)
production_controller = ProductionController(view)
release_controller = ReleaseController(view)
monitor_controller = MonitorController(view)
app = AppController(
    view, sample_controller, order_controller, monitor_controller,
    production_controller, release_controller,
)
app.run()
```

## Error Handling

Invalid main-menu choice (non-numeric or out-of-range): "잘못된
입력입니다.", re-show the menu — same convention used everywhere else.

## Testing

`ConsoleView.show_status_bar` tested via `capsys` (all four values appear
in output). `AppController` tested with `FakeView` plus recording stub
objects standing in for each sub-controller (same pattern `ConsoleMVC`'s
PoC used for its `AppController` tests) to verify dispatch routing for all
6 menu numbers plus exit; status bar values are tested separately with
real repositories (`tmp_path`) populated with known sample/order/queue
data, verifying the four computed numbers are correct. A final manual
smoke test walks every one of the 7 menu options once from a cold, empty
`data/` directory.

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-8-status-bar-final-wiring`, merged
via a PR the user reviews and merges manually.
