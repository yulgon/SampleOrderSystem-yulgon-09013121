# Phase 5 (Production Line) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 생산 라인 menu — 생산 현황 (head-of-queue detail), 대기 주문 확인 (full queue with cumulative expected-completion), 생산 완료 처리 (manually complete the head entry: restore stock, confirm the order, remove the entry). Add `delete()` to `ProductionQueueRepository`.

**Architecture:** `ProductionQueueRepository.list_all()`'s creation-id order IS FIFO order — the first entry is always "currently in production," with no separate status field needed. `ProductionController` holds `SampleRepository`, `OrderRepository`, and `ProductionQueueRepository` (same three-repository pattern as `OrderController`).

**Tech Stack:** Python 3, pytest (`tmp_path`).

## Global Constraints

- No wall-clock/timestamp tracking anywhere — completion is manual only, triggered by a menu action.
- "예상완료" is a **cumulative** duration: for the Nth entry in queue order, it's the sum of `total_time` for entries 1..N (itself included).
- 생산 완료 처리 always operates on the queue's head entry (`list_all()[0]`): adds `shortfall` (not `actual_qty`) back to the sample's stock, sets the order's status to `CONFIRMED`, then deletes the entry.
- All three menu actions show a distinct "nothing to do" message when the queue is empty, rather than blank output.
- No numeric input prompts in this controller — no retry-until-valid loops needed (all actions operate on the queue as a whole, not a user-specified id).
- Commit staging: `[RED]` then `[GREEN]`; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-5-production-line` — no direct commits to `main`.
- Tests use `tmp_path` for anything touching a repository.

---

### Task 1: `ProductionQueueRepository.delete()`

**Files:**
- Modify: `persistence/production_queue_repository.py`
- Modify: `tests/test_production_queue_repository.py`

**Interfaces:**
- Produces: `ProductionQueueRepository.delete(entry_id: int) -> bool`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_production_queue_repository.py`:

```python
def test_delete_removes_entry_and_returns_true(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    entry = repo.create(_make_entry())
    assert repo.delete(entry.entry_id) is True
    assert repo.list_all() == []


def test_delete_returns_false_for_missing_id(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry())
    assert repo.delete(999) is False
    assert len(repo.list_all()) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_production_queue_repository.py -v`
Expected: FAIL with `AttributeError: 'ProductionQueueRepository' object has no attribute 'delete'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_production_queue_repository.py
git commit -m "[RED] add failing tests for ProductionQueueRepository.delete()"
```

- [ ] **Step 4: Write minimal implementation**

Add to `persistence/production_queue_repository.py` (as a method on `ProductionQueueRepository`):

```python
    def delete(self, entry_id):
        return self._repo.delete(entry_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_production_queue_repository.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add persistence/production_queue_repository.py
git commit -m "[GREEN] implement ProductionQueueRepository.delete()"
```

---

### Task 2: `ProductionController`

**Files:**
- Create: `controller/production_controller.py`
- Test: `tests/test_production_controller.py`

**Interfaces:**
- Consumes: `FakeView`; `OrderStatus` from `model/order.py`; `SampleRepository`, `OrderRepository`, `ProductionQueueRepository`
- Produces: `ProductionController(view, base_dir="data")` with `.run() -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_production_controller.py`:

```python
import math

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from controller.production_controller import ProductionController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


def _setup_queued_order(base_dir, stock=2, yield_rate=0.5, avg_time=2.0, qty=10):
    samples = SampleRepository(base_dir=base_dir)
    orders = OrderRepository(base_dir=base_dir)
    queue = ProductionQueueRepository(base_dir=base_dir)

    sample = samples.create(
        Sample(name="Sample A", avg_production_time=avg_time, yield_rate=yield_rate, stock=stock)
    )
    order = orders.create(
        Order(sample_id=sample.sample_id, customer="Acme", qty=qty, status=OrderStatus.PRODUCING)
    )
    shortfall = qty - stock
    actual_qty = math.ceil(shortfall / yield_rate)
    total_time = avg_time * actual_qty
    entry = queue.create(
        ProductionQueueEntry(
            order_id=order.order_id, sample_id=sample.sample_id,
            shortfall=shortfall, actual_qty=actual_qty, total_time=total_time,
        )
    )
    return sample, order, entry


def test_current_status_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "생산 중인 항목이 없습니다." in view.messages


def test_current_status_shows_head_entry(tmp_path):
    sample, order, entry = _setup_queued_order(str(tmp_path))

    view = FakeView(inputs=["1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any(
        f"주문번호={order.order_id}" in m and f"예상완료={entry.total_time}" in m
        for m in view.messages
    )


def test_pending_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["2", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "대기 중인 생산이 없습니다." in view.messages


def test_pending_shows_cumulative_expected_completion(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample = samples.create(Sample(name="Sample A", avg_production_time=2.0, yield_rate=0.5, stock=0))
    order1 = orders.create(Order(sample_id=sample.sample_id, customer="A", qty=5, status=OrderStatus.PRODUCING))
    order2 = orders.create(Order(sample_id=sample.sample_id, customer="B", qty=5, status=OrderStatus.PRODUCING))
    queue.create(ProductionQueueEntry(
        order_id=order1.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))
    queue.create(ProductionQueueEntry(
        order_id=order2.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))

    view = FakeView(inputs=["2", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any("순서=1" in m and "예상완료=20.0" in m for m in view.messages)
    assert any("순서=2" in m and "예상완료=40.0" in m for m in view.messages)


def test_complete_current_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["3", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "완료 처리할 생산이 없습니다." in view.messages


def test_complete_current_updates_stock_order_and_removes_entry(tmp_path):
    sample, order, entry = _setup_queued_order(str(tmp_path), stock=2, yield_rate=0.5, avg_time=2.0, qty=10)

    view = FakeView(inputs=["3", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    remaining_queue = ProductionQueueRepository(base_dir=str(tmp_path)).list_all()

    assert updated_sample.stock == 2 + entry.shortfall
    assert updated_order.status == OrderStatus.CONFIRMED
    assert remaining_queue == []


def test_completing_head_promotes_next_entry(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample = samples.create(Sample(name="Sample A", avg_production_time=2.0, yield_rate=0.5, stock=0))
    order1 = orders.create(Order(sample_id=sample.sample_id, customer="A", qty=5, status=OrderStatus.PRODUCING))
    order2 = orders.create(Order(sample_id=sample.sample_id, customer="B", qty=5, status=OrderStatus.PRODUCING))
    queue.create(ProductionQueueEntry(
        order_id=order1.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))
    queue.create(ProductionQueueEntry(
        order_id=order2.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))

    view = FakeView(inputs=["3", "1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any(f"주문번호={order2.order_id}" in m for m in view.messages)


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_production_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller.production_controller'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_production_controller.py
git commit -m "[RED] add failing tests for ProductionController"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/production_controller.py`:

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
                self.view.show_message("잘못된 입력입니다.")

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
        self.view.show_message(
            f"생산 완료 처리: 주문ID={entry.order_id}, 재고 +{entry.shortfall}, "
            f"상태={OrderStatus.CONFIRMED}"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_production_controller.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/production_controller.py
git commit -m "[GREEN] implement ProductionController"
```

---

### Task 3: `main.py` wiring + manual smoke test

**Files:**
- Modify: `main.py`

**No new tests** — integration wiring, verified by the existing suite plus a manual smoke test.

- [ ] **Step 1: Update main.py's menu**

Replace `main.py`'s contents with:

```python
from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)
    production_controller = ProductionController(view)

    while True:
        view.show_menu(
            "메인 메뉴",
            [
                (0, "종료"),
                (1, "시료 관리"),
                (2, "시료 주문"),
                (3, "주문 (승인/거절)"),
                (4, "생산 라인"),
            ],
        )
        choice = view.get_input("메뉴 번호를 입력하세요: ")

        if choice == "0":
            return
        elif choice == "1":
            sample_controller.run()
        elif choice == "2":
            order_controller.run_reserve()
        elif choice == "3":
            order_controller.run_approve_reject()
        elif choice == "4":
            production_controller.run()
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1-2 tests pass (75 + 2 + 8 = 85 passed)

- [ ] **Step 3: Manual smoke test — register a low-stock sample, reserve more than available, approve it into production, view status, complete it, exit**

```bash
mkdir -p data
printf "1\n1\nSample A\n2.0\n0.5\n2\n4\n2\n1\nAcme\n10\n3\n2\n1\n4\n4\n1\n4\n3\n4\n0\n" | python main.py
```

(inputs: 시료관리 → register stock=2, yield=0.5, avg_time=2.0 → back → 시료주문 →
sample id 1, customer, qty 10 → 주문승인/거절 → 승인 → order id 1 → back →
생산라인 → 생산현황 → back → 생산완료처리 → back → exit)

Expected: after registering with insufficient stock (2 < 10), approval routes the
order to `PRODUCING` and queues a `ProductionQueueEntry` (shortfall=8, yield=0.5 →
actual_qty=16, total_time=32.0). 생산 현황 shows this entry. 생산 완료 처리 adds 8
back to stock (2 → 10) and confirms the order. No tracebacks. Confirm
`data/samples.json` shows `stock: 10`, `data/orders.json` shows the order
`status: "CONFIRMED"`, and the production queue's JSON file (`data/production_queue.json`)
is empty (`[]`). Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire 생산 라인 into the temporary main menu"
```

## Self-Review Notes

- **Spec coverage:** 생산 현황/대기 주문 확인/생산 완료 처리 each with empty-queue and populated-queue behavior, cumulative expected-completion math, head-promotion after completion — every design-spec behavior has a task and test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `ProductionController(view, base_dir="data")` matches how `main.py` (Task 3) instantiates it; `ProductionQueueRepository.delete(entry_id)` matches the pattern already established by `SampleRepository`/`OrderRepository`'s own `delete()`.
