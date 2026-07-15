# Phase 8 (Status Bar + Final Wiring) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `ConsoleView.show_status_bar()`, build a real `AppController` (PRD §6's authoritative menu numbering, live status bar computed from real repositories), and rewrite `main.py` to be minimal — replacing the temporary inline menu accumulated across Phases 2-7.

**Architecture:** `AppController` builds its own `SampleRepository`/`OrderRepository`/`ProductionQueueRepository` for status-bar aggregation (same "each component builds its own repositories" pattern used everywhere else) and holds a dispatch dict mapping menu numbers to the 6 sub-controllers' entry methods (same shape as `ConsoleMVC`'s PoC `AppController`).

**Tech Stack:** Python 3, pytest (`tmp_path`, `capsys`).

## Global Constraints

- Menu numbering matches PRD §6 exactly: 1 시료 관리, 2 시료 주문, 3 주문(승인/거절), 4 모니터링, 5 출고 처리, 6 생산 라인, 7 종료.
- Status bar values, recomputed every loop iteration (no caching):
  - 등록시료 = `len(SampleRepository.list_all())`
  - 총재고 = `sum(sample.stock for sample in SampleRepository.list_all())`
  - 전체주문 = count of orders with `status != OrderStatus.REJECTED` (same rule as Phase 7's 전체주문/모니터링 view)
  - 대기중인생산라인 = `len(ProductionQueueRepository.list_all())`
- Invalid menu choice (non-numeric or out-of-range): "잘못된 입력입니다.", re-show the menu.
- Choice `"7"` exits with a "프로그램을 종료합니다." message.
- Commit staging: `[RED]` then `[GREEN]`; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-8-status-bar-final-wiring` — no direct commits to `main`.
- Tests use `tmp_path`/`capsys`.

---

### Task 1: `ConsoleView.show_status_bar()`

**Files:**
- Modify: `view/console_view.py`
- Modify: `tests/test_console_view.py`

**Interfaces:**
- Produces: `ConsoleView.show_status_bar(registered_samples, total_stock, total_orders, waiting_lines) -> None`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_console_view.py`:

```python
def test_show_status_bar_prints_all_four_values(capsys):
    view = ConsoleView()
    view.show_status_bar(registered_samples=2, total_stock=15, total_orders=3, waiting_lines=1)
    captured = capsys.readouterr()
    assert "등록시료: 2" in captured.out
    assert "총 재고: 15" in captured.out
    assert "전체주문: 3" in captured.out
    assert "대기중인 생산라인: 1" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_console_view.py -v`
Expected: FAIL with `AttributeError: 'ConsoleView' object has no attribute 'show_status_bar'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_console_view.py
git commit -m "[RED] add failing test for ConsoleView.show_status_bar()"
```

- [ ] **Step 4: Write minimal implementation**

Add to `view/console_view.py` (as a method on `ConsoleView`):

```python
    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        print(
            f"[상태] 등록시료: {registered_samples} | 총 재고: {total_stock} | "
            f"전체주문: {total_orders} | 대기중인 생산라인: {waiting_lines}"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_console_view.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add view/console_view.py
git commit -m "[GREEN] implement ConsoleView.show_status_bar()"
```

---

### Task 2: `AppController`

**Files:**
- Create: `controller/app_controller.py`
- Modify: `tests/fakes.py` (add `show_status_bar` recording to `FakeView`)
- Test: `tests/test_app_controller.py`

**Interfaces:**
- Consumes: `FakeView` from `tests/fakes.py`; `OrderStatus` from `model/order.py`; `SampleRepository`, `OrderRepository`, `ProductionQueueRepository`
- Produces: `AppController(view, sample_controller, order_controller, monitor_controller, production_controller, release_controller, base_dir="data")` with `.run() -> None`

- [ ] **Step 1: Write the failing test**

Add to `tests/fakes.py` (a new method on the existing `FakeView` class):

```python
    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        self.status_bars.append((registered_samples, total_stock, total_orders, waiting_lines))
```

And add `self.status_bars = []` to `FakeView.__init__` alongside the existing `self.messages = []` / `self.menus = []` lines.

Create `tests/test_app_controller.py`:

```python
from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from controller.app_controller import AppController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


class RecordingHandler:
    def __init__(self):
        self.calls = 0

    def run(self):
        self.calls += 1

    run_reserve = run
    run_approve_reject = run


class OrderStub:
    def __init__(self):
        self.reserve_calls = 0
        self.approve_reject_calls = 0

    def run_reserve(self):
        self.reserve_calls += 1

    def run_approve_reject(self):
        self.approve_reject_calls += 1


def _make_controller(tmp_path, inputs, order=None):
    sample = RecordingHandler()
    order = order or RecordingHandler()
    monitor = RecordingHandler()
    production = RecordingHandler()
    release = RecordingHandler()
    view = FakeView(inputs=inputs)
    controller = AppController(
        view, sample, order, monitor, production, release, base_dir=str(tmp_path)
    )
    return controller, view, sample, order, monitor, production, release


def test_selecting_sample_menu_dispatches_to_sample_controller(tmp_path):
    controller, view, sample, *_ = _make_controller(tmp_path, ["1", "7"])
    controller.run()
    assert sample.calls == 1


def test_selecting_exit_stops_the_loop_without_dispatching(tmp_path):
    controller, view, sample, *_ = _make_controller(tmp_path, ["7"])
    controller.run()
    assert sample.calls == 0
    assert "종료" in view.messages[-1]


def test_invalid_menu_number_shows_error_and_reprompts(tmp_path):
    controller, view, *_ = _make_controller(tmp_path, ["99", "7"])
    controller.run()
    assert "잘못된 입력입니다." in view.messages


def test_non_numeric_input_shows_error_and_reprompts(tmp_path):
    controller, view, *_ = _make_controller(tmp_path, ["abc", "7"])
    controller.run()
    assert "잘못된 입력입니다." in view.messages


def test_selecting_order_menu_dispatches_to_run_reserve(tmp_path):
    order = OrderStub()
    controller, view, *_ = _make_controller(tmp_path, ["2", "7"], order=order)
    controller.run()
    assert order.reserve_calls == 1
    assert order.approve_reject_calls == 0


def test_selecting_approve_reject_menu_dispatches_to_run_approve_reject(tmp_path):
    order = OrderStub()
    controller, view, *_ = _make_controller(tmp_path, ["3", "7"], order=order)
    controller.run()
    assert order.approve_reject_calls == 1


def test_status_bar_reflects_real_repository_state(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample1 = samples.create(Sample(name="A", avg_production_time=2.0, yield_rate=0.9, stock=5))
    samples.create(Sample(name="B", avg_production_time=2.0, yield_rate=0.9, stock=3))
    order1 = orders.create(
        Order(sample_id=sample1.sample_id, customer="X", qty=1, status=OrderStatus.RESERVED)
    )
    orders.create(
        Order(sample_id=sample1.sample_id, customer="Y", qty=1, status=OrderStatus.REJECTED)
    )
    queue.create(
        ProductionQueueEntry(
            order_id=order1.order_id, sample_id=sample1.sample_id,
            shortfall=1, actual_qty=2, total_time=4.0,
        )
    )

    controller, view, *_ = _make_controller(tmp_path, ["7"])
    controller.run()

    # 2 samples registered, stock 5+3=8, 1 non-rejected order, 1 queue entry
    assert view.status_bars[0] == (2, 8, 1, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller.app_controller'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/fakes.py tests/test_app_controller.py
git commit -m "[RED] add failing tests for AppController"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/app_controller.py`:

```python
from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class AppController:
    MENU_TITLE = "메인 메뉴"
    MENU_OPTIONS = [
        (1, "시료 관리"),
        (2, "시료 주문"),
        (3, "주문 (승인/거절)"),
        (4, "모니터링"),
        (5, "출고 처리"),
        (6, "생산 라인"),
        (7, "종료"),
    ]

    def __init__(self, view, sample_controller, order_controller, monitor_controller,
                 production_controller, release_controller, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)
        self._handlers = {
            1: sample_controller.run,
            2: order_controller.run_reserve,
            3: order_controller.run_approve_reject,
            4: monitor_controller.run,
            5: release_controller.run,
            6: production_controller.run,
        }

    def run(self):
        while True:
            self._show_status_bar()
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "7":
                self.view.show_message("프로그램을 종료합니다.")
                return

            try:
                menu_number = int(choice)
            except ValueError:
                self.view.show_message("잘못된 입력입니다.")
                continue

            handler = self._handlers.get(menu_number)
            if handler is None:
                self.view.show_message("잘못된 입력입니다.")
                continue

            handler()

    def _show_status_bar(self):
        samples = self.samples.list_all()
        orders = self.orders.list_all()
        self.view.show_status_bar(
            registered_samples=len(samples),
            total_stock=sum(sample.stock for sample in samples),
            total_orders=sum(1 for order in orders if order.status != OrderStatus.REJECTED),
            waiting_lines=len(self.queue.list_all()),
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_app_controller.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/app_controller.py
git commit -m "[GREEN] implement AppController with live status bar"
```

---

### Task 3: `main.py` final rewrite + manual smoke test

**Files:**
- Modify: `main.py` (full rewrite)

**No new tests** — integration wiring, verified by the existing suite plus a manual smoke test walking every menu option once.

- [ ] **Step 1: Rewrite main.py**

Replace `main.py`'s contents with:

```python
from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.release_controller import ReleaseController
from controller.monitor_controller import MonitorController
from controller.app_controller import AppController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)
    production_controller = ProductionController(view)
    release_controller = ReleaseController(view)
    monitor_controller = MonitorController(view)

    app = AppController(
        view,
        sample_controller,
        order_controller,
        monitor_controller,
        production_controller,
        release_controller,
    )
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1-2 tests pass (97 + 1 + 7 = 105 passed)

- [ ] **Step 3: Manual smoke test — walk every one of the 7 menu options once from a cold, empty `data/` directory**

Before running, trace the exact stdin token sequence against `AppController`'s and each sub-controller's real menu-loop code — this project has repeatedly had off-by-one stdin sequences in prior phases' pre-written smoke tests. Build the sequence to exercise, in order: 1 (시료 관리: register a sample, list, search, back), 2 (시료 주문: reserve an order against that sample, with qty exceeding its stock so it queues into production), 3 (주문 승인/거절: list pending, approve the order — insufficient stock → PRODUCING), 6 (생산 라인: view 생산 현황, complete production → CONFIRMED), 5 (출고 처리: release that order → RELEASE), 4 (모니터링: 주문량 확인, 재고량 확인), 7 (종료).

Expected: the status bar updates correctly at each loop iteration (등록시료 increases after registering; 총재고 changes as stock is consumed/restored; 전체주문 reflects the one non-rejected order; 대기중인생산라인 shows 1 while queued, 0 after production completes); every menu is reachable; no tracebacks. Confirm `data/samples.json`, `data/orders.json`, and `data/production_queue.json` end in the expected final states (order `RELEASE`, queue empty). Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] replace temporary main.py menu with AppController"
```

## Self-Review Notes

- **Spec coverage:** live status bar (all 4 values, recomputed each iteration), PRD-numbered dispatch (1-7), invalid-choice handling, exit — every design-spec behavior has a task and test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `AppController`'s constructor signature and dispatch-table method names (`run`, `run_reserve`, `run_approve_reject`) match the real sub-controllers from Phases 2-7 exactly; `FakeView.show_status_bar`'s parameter order matches `ConsoleView.show_status_bar`'s (Task 1) exactly.
