# Phase 10 (Console UI Styling) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ANSI color styling and a program banner to the console UI — no new dependency, no business logic changes, and zero changes to any existing test (all 106 tests must pass unmodified throughout).

**Architecture:** `ConsoleView` gains a `Color` constants class, a Windows-ANSI-enable step (stdlib `ctypes` only), and two new output methods (`show_success`, `show_error`) plus a `show_banner` method; `show_menu`/`show_status_bar` get colorized. The 6 existing controllers re-route their existing `show_message(...)` calls to `show_error`/`show_success` by intent, with no wording changes. `tests/fakes.py`'s `FakeView` routes the two new methods into the same `.messages` list `show_message` already uses, so every existing controller test keeps working unchanged.

**Tech Stack:** Python 3, stdlib only (`ctypes` for the Windows console-mode step), pytest (`capsys`).

## Global Constraints

- No new external dependency (no `colorama`) — pure ANSI escape codes plus a stdlib-only Windows console-mode enable step.
- Color scheme: banner = bold cyan, menu titles/status bar = cyan, success messages = green, error messages = red, plain informational output = uncolored (unchanged).
- `FakeView.show_error`/`FakeView.show_success` both append to the same `self.messages` list `show_message` already uses — this is what keeps all 106 existing tests passing without modification.
- No message text changes anywhere — only which view method delivers each existing string.
- No new business logic, no new menu items.
- Commit staging: `[RED]`/`[GREEN]` where a pytest cycle applies (Task 1); Task 2 (controller routing) has no new tests of its own, so it's `[GREEN]`-only, verified by the full existing suite; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-10-console-ui-styling` — no direct commits to `main`.

---

### Task 1: `ConsoleView` color/banner infrastructure + `FakeView` compatibility

**Files:**
- Modify: `view/console_view.py` (full rewrite)
- Modify: `tests/fakes.py` (add `show_error`/`show_success`)
- Modify: `tests/test_console_view.py` (append new tests)

**Interfaces:**
- Produces: `Color` class (`RESET`, `BOLD`, `CYAN`, `GREEN`, `RED`) in `view/console_view.py`
- Produces: `ConsoleView.show_success(message) -> None`, `ConsoleView.show_error(message) -> None`, `ConsoleView.show_banner() -> None`
- Produces: `FakeView.show_error(message) -> None`, `FakeView.show_success(message) -> None` (both append to `self.messages`)

- [ ] **Step 1: Write the failing test**

Modify `tests/test_console_view.py`'s import line to also bring in `Color`:

```python
from view.console_view import ConsoleView, Color
```

Append these tests to the end of the file:

```python
def test_show_success_wraps_message_in_green(capsys):
    view = ConsoleView()
    view.show_success("완료")
    captured = capsys.readouterr()
    assert Color.GREEN in captured.out
    assert "완료" in captured.out
    assert Color.RESET in captured.out


def test_show_error_wraps_message_in_red(capsys):
    view = ConsoleView()
    view.show_error("오류")
    captured = capsys.readouterr()
    assert Color.RED in captured.out
    assert "오류" in captured.out
    assert Color.RESET in captured.out


def test_show_banner_prints_program_name_in_cyan(capsys):
    view = ConsoleView()
    view.show_banner()
    captured = capsys.readouterr()
    assert Color.CYAN in captured.out
    assert "S-Semi" in captured.out


def test_show_menu_includes_cyan_color_code(capsys):
    view = ConsoleView()
    view.show_menu("메인 메뉴", [(1, "옵션")])
    captured = capsys.readouterr()
    assert Color.CYAN in captured.out


def test_show_status_bar_includes_cyan_color_code(capsys):
    view = ConsoleView()
    view.show_status_bar(registered_samples=0, total_stock=0, total_orders=0, waiting_lines=0)
    captured = capsys.readouterr()
    assert Color.CYAN in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_console_view.py -v`
Expected: FAIL with `ImportError: cannot import name 'Color' from 'view.console_view'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_console_view.py
git commit -m "[RED] add failing tests for ConsoleView color/banner methods"
```

- [ ] **Step 4: Write minimal implementation**

Replace `view/console_view.py`'s full contents with:

```python
import sys


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"


def _enable_windows_ansi():
    if sys.platform != "win32":
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


class ConsoleView:
    def __init__(self):
        _enable_windows_ansi()

    def show_message(self, message):
        print(message)

    def show_success(self, message):
        print(f"{Color.GREEN}{message}{Color.RESET}")

    def show_error(self, message):
        print(f"{Color.RED}{message}{Color.RESET}")

    def show_menu(self, title, options):
        print(f"\n{Color.CYAN}{Color.BOLD}=== {title} ==={Color.RESET}")
        for number, label in options:
            print(f"{number}. {label}")

    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        print(
            f"{Color.CYAN}[상태] 등록시료: {registered_samples} | 총 재고: {total_stock} | "
            f"전체주문: {total_orders} | 대기중인 생산라인: {waiting_lines}{Color.RESET}"
        )

    def show_banner(self):
        print(f"{Color.CYAN}{Color.BOLD}")
        print("=" * 50)
        print("   S-Semi SampleOrderSystem")
        print("=" * 50)
        print(Color.RESET)

    def get_input(self, prompt):
        return input(prompt)
```

Add to `tests/fakes.py` (two new methods on the existing `FakeView` class,
alongside `show_message`):

```python
    def show_error(self, message):
        self.messages.append(message)

    def show_success(self, message):
        self.messages.append(message)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_console_view.py -v`
Expected: 8 passed (3 existing + 5 new)

- [ ] **Step 6: Run the full suite to confirm zero regressions from the `FakeView` change**

Run: `pytest -v`
Expected: 106 passed (no test file besides `test_console_view.py` should show any change in outcome, since `FakeView`'s change is purely additive)

- [ ] **Step 7: Commit the implementation**

```bash
git add view/console_view.py tests/fakes.py
git commit -m "[GREEN] add ConsoleView color/banner methods and FakeView compatibility"
```

---

### Task 2: Route controllers to `show_error`/`show_success`

**Files:**
- Modify: `controller/sample_controller.py`
- Modify: `controller/order_controller.py`
- Modify: `controller/production_controller.py`
- Modify: `controller/release_controller.py`
- Modify: `controller/monitor_controller.py`
- Modify: `controller/app_controller.py`

**No new tests** — every existing test in `tests/test_sample_controller.py`,
`tests/test_order_controller.py`, `tests/test_production_controller.py`,
`tests/test_release_controller.py`, `tests/test_monitor_controller.py`,
`tests/test_app_controller.py`, and `tests/test_end_to_end.py` must pass
**unmodified**, because `FakeView.show_error`/`show_success` (Task 1)
append to the same `.messages` list `show_message` did. This task changes
*which method* delivers each string, not the string content.

- [ ] **Step 1: Rewrite `controller/sample_controller.py`**

Replace its full contents with (only the view-method calls changed from
`show_message` — everything else identical to before):

```python
from model.sample import Sample
from persistence.sample_repository import SampleRepository


class SampleController:
    MENU_TITLE = "시료 관리"
    MENU_OPTIONS = [(1, "시료 등록"), (2, "시료 조회"), (3, "시료 검색"), (4, "돌아가기")]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.repository = SampleRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._register()
            elif choice == "2":
                self._list()
            elif choice == "3":
                self._search()
            elif choice == "4":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _prompt_float(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = float(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_error(error_message)
                continue
            return value

    def _prompt_int(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_error(error_message)
                continue
            return value

    def _register(self):
        name = self.view.get_input("시료명: ")
        avg_production_time = self._prompt_float(
            "평균 생산시간: ",
            "평균 생산시간은 0보다 커야 합니다.",
            lambda v: v > 0,
        )
        yield_rate = self._prompt_float(
            "수율: ",
            "수율은 0보다 크고 1 이하여야 합니다.",
            lambda v: 0 < v <= 1,
        )
        stock = self._prompt_int(
            "현재 재고: ",
            "재고는 0 이상이어야 합니다.",
            lambda v: v >= 0,
        )
        sample = self.repository.create(
            Sample(
                name=name,
                avg_production_time=avg_production_time,
                yield_rate=yield_rate,
                stock=stock,
            )
        )
        self.view.show_success(
            f"시료 등록 완료: ID={sample.sample_id}, 이름={sample.name}, "
            f"평균생산시간={sample.avg_production_time}, 수율={sample.yield_rate}, "
            f"재고={sample.stock}"
        )

    def _list(self):
        samples = self.repository.list_all()
        if not samples:
            self.view.show_message("등록된 시료가 없습니다.")
            return
        for sample in samples:
            self.view.show_message(
                f"ID={sample.sample_id}, 이름={sample.name}, "
                f"평균생산시간={sample.avg_production_time}, 수율={sample.yield_rate}, "
                f"재고={sample.stock}"
            )

    def _search(self):
        keyword = self.view.get_input("검색어(이름): ")
        matches = [s for s in self.repository.list_all() if keyword in s.name]
        if not matches:
            self.view.show_message("일치하는 시료가 없습니다.")
            return
        for sample in matches:
            self.view.show_message(
                f"ID={sample.sample_id}, 이름={sample.name}, 재고={sample.stock}"
            )
```

- [ ] **Step 2: Rewrite `controller/order_controller.py`**

Replace its full contents with:

```python
import math

from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class OrderController:
    APPROVE_MENU_TITLE = "주문 (승인/거절)"
    APPROVE_MENU_OPTIONS = [
        (1, "접수된 주문 목록"),
        (2, "주문 승인"),
        (3, "주문 거절"),
        (4, "돌아가기"),
    ]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)

    def run_reserve(self):
        sample = self._prompt_existing_sample()
        customer = self.view.get_input("고객명: ")
        qty = self._prompt_qty()
        order = self.orders.create(
            Order(sample_id=sample.sample_id, customer=customer, qty=qty, status=OrderStatus.RESERVED)
        )
        self.view.show_success(
            f"주문 접수 완료: ID={order.order_id}, 시료ID={order.sample_id}, "
            f"고객명={order.customer}, 수량={order.qty}, 상태={order.status}"
        )

    def _prompt_existing_sample(self):
        while True:
            raw = self.view.get_input("시료 ID: ")
            try:
                sample_id = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            sample = self.samples.get(sample_id)
            if sample is None:
                self.view.show_error("존재하지 않는 시료 ID입니다.")
                continue
            return sample

    def _prompt_qty(self):
        while True:
            raw = self.view.get_input("주문 수량: ")
            try:
                qty = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            if qty <= 0:
                self.view.show_error("주문 수량은 0보다 커야 합니다.")
                continue
            return qty

    def run_approve_reject(self):
        while True:
            self.view.show_menu(self.APPROVE_MENU_TITLE, self.APPROVE_MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._list_pending()
            elif choice == "2":
                self._approve()
            elif choice == "3":
                self._reject()
            elif choice == "4":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _list_pending(self):
        pending = [o for o in self.orders.list_all() if o.status == OrderStatus.RESERVED]
        if not pending:
            self.view.show_message("접수된 주문이 없습니다.")
            return
        for order in pending:
            self.view.show_message(
                f"ID={order.order_id}, 시료ID={order.sample_id}, "
                f"고객명={order.customer}, 수량={order.qty}"
            )

    def _prompt_pending_order(self):
        while True:
            raw = self.view.get_input("주문 ID: ")
            try:
                order_id = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.RESERVED:
                self.view.show_error("유효한 접수 주문이 아닙니다.")
                continue
            return order

    def _approve(self):
        order = self._prompt_pending_order()
        sample = self.samples.get(order.sample_id)

        if sample.stock >= order.qty:
            self.samples.update(sample.sample_id, {"stock": sample.stock - order.qty})
            self.orders.update(order.order_id, {"status": OrderStatus.CONFIRMED})
            self.view.show_success(
                f"승인 완료 (재고 차감): ID={order.order_id}, 상태={OrderStatus.CONFIRMED}"
            )
        else:
            shortfall = order.qty - sample.stock
            actual_qty = math.ceil(shortfall / sample.yield_rate)
            total_time = sample.avg_production_time * actual_qty
            self.queue.create(
                ProductionQueueEntry(
                    order_id=order.order_id,
                    sample_id=sample.sample_id,
                    shortfall=shortfall,
                    actual_qty=actual_qty,
                    total_time=total_time,
                )
            )
            self.orders.update(order.order_id, {"status": OrderStatus.PRODUCING})
            self.view.show_success(
                f"재고 부족 - 생산 등록: 주문ID={order.order_id}, 부족분={shortfall}, "
                f"실생산량={actual_qty}, 총생산시간={total_time}"
            )

    def _reject(self):
        order = self._prompt_pending_order()
        self.orders.update(order.order_id, {"status": OrderStatus.REJECTED})
        self.view.show_success(
            f"주문 거절 완료: ID={order.order_id}, 상태={OrderStatus.REJECTED}"
        )
```

- [ ] **Step 3: Rewrite `controller/production_controller.py`**

Replace its full contents with:

```python
from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class ProductionController:
    MENU_TITLE = "생산 라인"
    MENU_OPTIONS = [(1, "생산 현황"), (2, "대기 주문 확인"), (3, "생산 완료 처리"), (4, "돌아가기")]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._show_current()
            elif choice == "2":
                self._show_pending()
            elif choice == "3":
                self._complete_current()
            elif choice == "4":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _describe(self, position, entry, expected_completion):
        order = self.orders.get(entry.order_id)
        sample = self.samples.get(entry.sample_id)
        return (
            f"순서={position}, 주문번호={entry.order_id}, 시료={sample.name}, "
            f"주문량={order.qty}, 부족분={entry.shortfall}, 실생산량={entry.actual_qty}, "
            f"예상완료={expected_completion}"
        )

    def _show_current(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("생산 중인 항목이 없습니다.")
            return
        head = queue[0]
        self.view.show_message(self._describe(1, head, head.total_time))

    def _show_pending(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("대기 중인 생산이 없습니다.")
            return
        cumulative = 0
        for position, entry in enumerate(queue, start=1):
            cumulative += entry.total_time
            self.view.show_message(self._describe(position, entry, cumulative))

    def _complete_current(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("완료 처리할 생산이 없습니다.")
            return
        entry = queue[0]
        sample = self.samples.get(entry.sample_id)
        self.samples.update(sample.sample_id, {"stock": sample.stock + entry.shortfall})
        self.orders.update(entry.order_id, {"status": OrderStatus.CONFIRMED})
        self.queue.delete(entry.entry_id)
        self.view.show_success(
            f"생산 완료 처리: 주문ID={entry.order_id}, 재고 +{entry.shortfall}, "
            f"상태={OrderStatus.CONFIRMED}"
        )
```

- [ ] **Step 4: Rewrite `controller/release_controller.py`**

Replace its full contents with:

```python
from model.order import OrderStatus
from persistence.order_repository import OrderRepository


class ReleaseController:
    def __init__(self, view, base_dir="data"):
        self.view = view
        self.orders = OrderRepository(base_dir=base_dir)

    def run(self):
        order = self._prompt_confirmed_order()
        self.orders.update(order.order_id, {"status": OrderStatus.RELEASE})
        self.view.show_success(
            f"출고 완료: 주문ID={order.order_id}, 상태={OrderStatus.RELEASE}"
        )

    def _prompt_confirmed_order(self):
        while True:
            raw = self.view.get_input("주문 ID: ")
            try:
                order_id = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.CONFIRMED:
                self.view.show_error("출고 가능한(CONFIRMED) 주문이 아닙니다.")
                continue
            return order
```

- [ ] **Step 5: Rewrite `controller/monitor_controller.py`**

Replace its full contents with (only the invalid-choice line changes):

```python
from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.sample_repository import SampleRepository


class MonitorController:
    MENU_TITLE = "모니터링"
    MENU_OPTIONS = [(1, "주문량 확인"), (2, "재고량 확인"), (3, "돌아가기")]
    VOLUME_STATUSES = (
        OrderStatus.RESERVED,
        OrderStatus.CONFIRMED,
        OrderStatus.PRODUCING,
        OrderStatus.RELEASE,
    )
    OUTSTANDING_STATUSES = (OrderStatus.RESERVED, OrderStatus.PRODUCING)

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._show_order_volume()
            elif choice == "2":
                self._show_stock_levels()
            elif choice == "3":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _show_order_volume(self):
        orders = self.orders.list_all()
        for status in self.VOLUME_STATUSES:
            count = sum(1 for order in orders if order.status == status)
            self.view.show_message(f"{status}: {count}건")

    def _show_stock_levels(self):
        samples = self.samples.list_all()
        if not samples:
            self.view.show_message("등록된 시료가 없습니다.")
            return
        orders = self.orders.list_all()
        for sample in samples:
            demand = sum(
                order.qty for order in orders
                if order.sample_id == sample.sample_id
                and order.status in self.OUTSTANDING_STATUSES
            )
            if sample.stock == 0:
                label = "고갈"
            elif sample.stock >= demand:
                label = "여유"
            else:
                label = "부족"
            self.view.show_message(
                f"시료={sample.name}, 재고={sample.stock}, 상태={label}"
            )
```

- [ ] **Step 6: Rewrite `controller/app_controller.py`**

Replace its full contents with (only the two invalid-choice lines change;
the exit message stays neutral `show_message`, matching the design's
scope — exiting isn't a success/failure event):

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
                self.view.show_error("잘못된 입력입니다.")
                continue

            handler = self._handlers.get(menu_number)
            if handler is None:
                self.view.show_error("잘못된 입력입니다.")
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

- [ ] **Step 7: Run the full suite to confirm all 106 tests still pass unmodified**

Run: `pytest -v`
Expected: 106 passed — every existing controller test still passes exactly
as before, since it asserts on message content in `view.messages`, and
`FakeView.show_error`/`show_success` append there too.

- [ ] **Step 8: Commit**

```bash
git add controller/sample_controller.py controller/order_controller.py controller/production_controller.py controller/release_controller.py controller/monitor_controller.py controller/app_controller.py
git commit -m "[GREEN] route controller error/success messages to show_error/show_success"
```

---

### Task 3: `main.py` banner wiring + manual visual smoke test

**Files:**
- Modify: `main.py`

**No new tests** — integration wiring, verified by the full suite plus a
manual visual check in a real terminal (this is the one thing `capsys`
genuinely cannot verify: whether the colors are *visible*, not just present
as escape codes in captured text).

- [ ] **Step 1: Add the banner call to main.py**

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
    view.show_banner()

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
Expected: 111 passed (106 prior + 5 new `ConsoleView` tests from Task 1)

- [ ] **Step 3: Manual visual smoke test in a real terminal**

Run `python main.py` in an actual terminal window (not just capturing
output) and visually confirm:
- The `S-Semi SampleOrderSystem` banner appears in bold cyan at startup.
- The main menu title and status bar line are cyan.
- Triggering an error (e.g. entering an invalid menu number) shows the
  message in red.
- Completing an action that succeeds (e.g. registering a sample) shows
  the confirmation in green.
- No raw escape-code garbage (e.g. literal `\033[36m` text) appears
  instead of actual color — if it does, the Windows ANSI-enable step
  isn't taking effect on this terminal and needs troubleshooting before
  this task is considered done.

Record what terminal/OS this was checked in, since ANSI rendering is
environment-dependent.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] show program banner at startup"
```

## Self-Review Notes

- **Spec coverage:** banner, colored menu/status bar, green success
  messages, red error messages, zero-touch to existing tests — every
  design-spec behavior has a task and verification step.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable
  code (full file rewrites, not partial diffs, to avoid ambiguity about
  exactly which lines changed).
- **Type consistency:** every controller still only calls methods that
  exist on both `ConsoleView` and `FakeView` (`show_message`,
  `show_error`, `show_success`, `show_menu`, `show_status_bar`,
  `get_input`) — no controller calls a method the other one lacks.
