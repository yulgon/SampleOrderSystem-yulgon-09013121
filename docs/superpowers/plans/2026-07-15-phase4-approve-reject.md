# Phase 4 (Approve/Reject) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `OrderController.run_approve_reject()` — list pending orders, approve (stock-sufficient → deduct + `CONFIRMED`; stock-insufficient → create a `ProductionQueueEntry` + `PRODUCING`), reject (→ `REJECTED`). Adds a new `ProductionQueueEntry` model and `ProductionQueueRepository` (create/list_all only).

**Architecture:** `model/production_queue_entry.py`'s `ProductionQueueEntry` is a plain dataclass (same to_dict/from_dict/`__post_init__` pattern as `Sample`/`Order`). `persistence/production_queue_repository.py`'s `ProductionQueueRepository` wraps a `JsonRepository("production_queue")`. `run_approve_reject()` is added to the existing `OrderController` class (alongside `run_reserve()` from Phase 3), gaining `SampleRepository` and `ProductionQueueRepository` as additional instance attributes.

**Tech Stack:** Python 3, `math.ceil` for the actual-quantity calculation, pytest (`tmp_path`).

## Global Constraints

- `actual_qty = ceil(shortfall / sample.yield_rate)`, `total_time = sample.avg_production_time * actual_qty` — both computed once at `ProductionQueueEntry` creation time.
- Stock is deducted ONLY on the sufficient-stock approval path. The insufficient-stock path creates a queue entry and sets `PRODUCING` — stock is untouched (added back in Phase 5, on production completion).
- An order id that doesn't exist or isn't `RESERVED` shows "유효한 접수 주문이 아닙니다." and re-prompts the SAME field (never bounces to the submenu).
- Invalid submenu choice: "잘못된 입력입니다.", re-show the submenu.
- No FIFO processing, no production-completion logic, no display screens for the queue — all Phase 5.
- Commit staging: `[RED]` then `[GREEN]`; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-4-approve-reject` — no direct commits to `main`.
- Tests use `tmp_path` for anything touching a repository.

---

### Task 1: `ProductionQueueEntry` dataclass

**Files:**
- Create: `model/production_queue_entry.py`
- Test: `tests/test_production_queue_entry.py`

**Interfaces:**
- Produces: `ProductionQueueEntry(order_id, sample_id, shortfall, actual_qty, total_time, entry_id=None)` with `to_dict()`/`from_dict()` (same id-inclusion-when-present pattern as `Sample`/`Order`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_production_queue_entry.py`:

```python
import pytest

from model.production_queue_entry import ProductionQueueEntry


def test_to_dict_includes_id_when_present():
    entry = ProductionQueueEntry(
        order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0, entry_id=1
    )
    assert entry.to_dict() == {
        "id": 1,
        "order_id": 1,
        "sample_id": 1,
        "shortfall": 8,
        "actual_qty": 16,
        "total_time": 32.0,
    }


def test_to_dict_omits_id_when_none():
    entry = ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0)
    assert "id" not in entry.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "order_id": 1, "sample_id": 1, "shortfall": 8, "actual_qty": 16, "total_time": 32.0}
    entry = ProductionQueueEntry.from_dict(data)
    assert entry.entry_id == 1
    assert entry.to_dict() == data


def test_raises_on_non_positive_shortfall():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=0, actual_qty=16, total_time=32.0)


def test_raises_on_non_positive_actual_qty():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=0, total_time=32.0)


def test_raises_on_non_positive_total_time():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_production_queue_entry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'model.production_queue_entry'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_production_queue_entry.py
git commit -m "[RED] add failing tests for ProductionQueueEntry"
```

- [ ] **Step 4: Write minimal implementation**

Create `model/production_queue_entry.py`:

```python
from dataclasses import dataclass


@dataclass
class ProductionQueueEntry:
    order_id: int
    sample_id: int
    shortfall: int
    actual_qty: int
    total_time: float
    entry_id: int = None

    def __post_init__(self):
        if self.shortfall <= 0:
            raise ValueError("shortfall must be positive")
        if self.actual_qty <= 0:
            raise ValueError("actual_qty must be positive")
        if self.total_time <= 0:
            raise ValueError("total_time must be positive")

    def to_dict(self):
        data = {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "shortfall": self.shortfall,
            "actual_qty": self.actual_qty,
            "total_time": self.total_time,
        }
        if self.entry_id is not None:
            data["id"] = self.entry_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            shortfall=data["shortfall"],
            actual_qty=data["actual_qty"],
            total_time=data["total_time"],
            entry_id=data.get("id"),
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_production_queue_entry.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add model/production_queue_entry.py
git commit -m "[GREEN] implement ProductionQueueEntry dataclass"
```

---

### Task 2: `ProductionQueueRepository`

**Files:**
- Create: `persistence/production_queue_repository.py`
- Test: `tests/test_production_queue_repository.py`

**Interfaces:**
- Consumes: `ProductionQueueEntry` from `model/production_queue_entry.py`; `JsonRepository` from `persistence/repository.py`
- Produces: `ProductionQueueRepository(base_dir="data")` with `.create(entry: ProductionQueueEntry) -> ProductionQueueEntry` and `.list_all() -> list[ProductionQueueEntry]`

- [ ] **Step 1: Write the failing test**

Create `tests/test_production_queue_repository.py`:

```python
from model.production_queue_entry import ProductionQueueEntry
from persistence.production_queue_repository import ProductionQueueRepository


def _make_entry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0):
    return ProductionQueueEntry(
        order_id=order_id, sample_id=sample_id, shortfall=shortfall,
        actual_qty=actual_qty, total_time=total_time,
    )


def test_create_returns_entry_with_assigned_id(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    created = repo.create(_make_entry())
    assert isinstance(created, ProductionQueueEntry)
    assert created.entry_id == 1
    assert created.order_id == 1


def test_list_all_returns_all_entries_in_order(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry(order_id=1))
    repo.create(_make_entry(order_id=2))
    assert [e.order_id for e in repo.list_all()] == [1, 2]


def test_create_ignores_preset_id_and_assigns_a_fresh_one(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry(order_id=1))
    second = ProductionQueueEntry(
        order_id=2, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0, entry_id=1,
    )
    created = repo.create(second)
    assert created.entry_id == 2
    assert len(repo.list_all()) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_production_queue_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'persistence.production_queue_repository'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_production_queue_repository.py
git commit -m "[RED] add failing tests for ProductionQueueRepository"
```

- [ ] **Step 4: Write minimal implementation**

Create `persistence/production_queue_repository.py`:

```python
from model.production_queue_entry import ProductionQueueEntry
from persistence.repository import JsonRepository


class ProductionQueueRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("production_queue", base_dir=base_dir)

    def create(self, entry):
        data = {k: v for k, v in entry.to_dict().items() if k != "id"}
        record = self._repo.create(data)
        return ProductionQueueEntry.from_dict(record)

    def list_all(self):
        return [ProductionQueueEntry.from_dict(record) for record in self._repo.list_all()]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_production_queue_repository.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add persistence/production_queue_repository.py
git commit -m "[GREEN] implement ProductionQueueRepository"
```

---

### Task 3: `OrderController.run_approve_reject()`

**Files:**
- Modify: `controller/order_controller.py` (add `run_approve_reject()` and helpers to the existing class; add imports for `math`, `ProductionQueueEntry`, `ProductionQueueRepository`, `SampleRepository`)
- Modify: `tests/test_order_controller.py` (append new tests)

**Interfaces:**
- Consumes: `FakeView`; `Sample` from `model/sample.py`; `Order`, `OrderStatus` from `model/order.py`; `ProductionQueueEntry` from `model/production_queue_entry.py`; `SampleRepository`, `OrderRepository`, `ProductionQueueRepository`
- Produces: `OrderController.run_approve_reject() -> None` (added to the existing class from Phase 3)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_order_controller.py` (add these imports at the top alongside the existing ones: `from model.production_queue_entry import ProductionQueueEntry` and `from persistence.production_queue_repository import ProductionQueueRepository`):

```python
def _register_sample(base_dir, stock=10, yield_rate=0.9, avg_time=2.0):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name="Sample A", avg_production_time=avg_time, yield_rate=yield_rate, stock=stock))


def _reserve_order(base_dir, sample_id, qty=5, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=OrderStatus.RESERVED))


def test_list_pending_shows_no_data_message_when_empty(tmp_path):
    view = FakeView(inputs=["1", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert "접수된 주문이 없습니다." in view.messages


def test_list_pending_shows_reserved_orders(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["1", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert any(f"ID={order.order_id}" in m for m in view.messages)


def test_approve_with_sufficient_stock_deducts_and_confirms(tmp_path):
    sample = _register_sample(str(tmp_path), stock=10)
    order = _reserve_order(str(tmp_path), sample.sample_id, qty=5)

    view = FakeView(inputs=["2", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    assert updated_order.status == OrderStatus.CONFIRMED
    assert updated_sample.stock == 5


def test_approve_with_insufficient_stock_queues_production(tmp_path):
    sample = _register_sample(str(tmp_path), stock=2, yield_rate=0.5, avg_time=2.0)
    order = _reserve_order(str(tmp_path), sample.sample_id, qty=10)

    view = FakeView(inputs=["2", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    queue_entries = ProductionQueueRepository(base_dir=str(tmp_path)).list_all()

    assert updated_order.status == OrderStatus.PRODUCING
    assert updated_sample.stock == 2
    assert len(queue_entries) == 1
    entry = queue_entries[0]
    assert entry.order_id == order.order_id
    assert entry.shortfall == 8
    assert entry.actual_qty == 16
    assert entry.total_time == 32.0


def test_reject_sets_rejected_status(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["3", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated_order.status == OrderStatus.REJECTED


def test_approve_retries_on_invalid_order_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["2", "999", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated_order.status == OrderStatus.CONFIRMED
    assert any("유효한 접수 주문이 아닙니다." in m for m in view.messages)


def test_invalid_submenu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert "잘못된 입력입니다." in view.messages
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_order_controller.py -v`
Expected: FAIL with `AttributeError: 'OrderController' object has no attribute 'run_approve_reject'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_order_controller.py
git commit -m "[RED] add failing tests for OrderController.run_approve_reject()"
```

- [ ] **Step 4: Write minimal implementation**

Rewrite `controller/order_controller.py` in full:

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
        self.view.show_message(
            f"주문 접수 완료: ID={order.order_id}, 시료ID={order.sample_id}, "
            f"고객명={order.customer}, 수량={order.qty}, 상태={order.status}"
        )

    def _prompt_existing_sample(self):
        while True:
            raw = self.view.get_input("시료 ID: ")
            try:
                sample_id = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            sample = self.samples.get(sample_id)
            if sample is None:
                self.view.show_message("존재하지 않는 시료 ID입니다.")
                continue
            return sample

    def _prompt_qty(self):
        while True:
            raw = self.view.get_input("주문 수량: ")
            try:
                qty = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if qty <= 0:
                self.view.show_message("주문 수량은 0보다 커야 합니다.")
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
                self.view.show_message("잘못된 입력입니다.")

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
                self.view.show_message("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.RESERVED:
                self.view.show_message("유효한 접수 주문이 아닙니다.")
                continue
            return order

    def _approve(self):
        order = self._prompt_pending_order()
        sample = self.samples.get(order.sample_id)

        if sample.stock >= order.qty:
            self.samples.update(sample.sample_id, {"stock": sample.stock - order.qty})
            self.orders.update(order.order_id, {"status": OrderStatus.CONFIRMED})
            self.view.show_message(
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
            self.view.show_message(
                f"재고 부족 - 생산 등록: 주문ID={order.order_id}, 부족분={shortfall}, "
                f"실생산량={actual_qty}, 총생산시간={total_time}"
            )

    def _reject(self):
        order = self._prompt_pending_order()
        self.orders.update(order.order_id, {"status": OrderStatus.REJECTED})
        self.view.show_message(
            f"주문 거절 완료: ID={order.order_id}, 상태={OrderStatus.REJECTED}"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_order_controller.py -v`
Expected: 13 passed (5 from Phase 3 + 8 new)

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/order_controller.py
git commit -m "[GREEN] implement OrderController.run_approve_reject()"
```

---

### Task 4: `main.py` wiring + manual smoke test

**Files:**
- Modify: `main.py`

**No new tests** — integration wiring, verified by the existing suite plus a manual smoke test.

- [ ] **Step 1: Update main.py's menu**

Replace `main.py`'s menu section to add option 3:

```python
from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)

    while True:
        view.show_menu(
            "메인 메뉴",
            [(0, "종료"), (1, "시료 관리"), (2, "시료 주문"), (3, "주문 (승인/거절)")],
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
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1-3 tests pass (56 + 6 + 3 + 8 = 73 passed)

- [ ] **Step 3: Manual smoke test — register, reserve, approve, exit**

```bash
mkdir -p data
printf "1\n1\nSample A\n2.5\n0.9\n10\n4\n2\n1\nAcme\n5\n3\n2\n1\n4\n0\n" | python main.py
```

(inputs: 시료관리 → register stock=10 → back → 시료주문 → sample id 1, customer, qty 5 →
주문승인/거절 → 승인 → order id 1 → back → exit)

Expected: prints the main menu throughout, registers one sample, reserves one order,
approves it — since stock(10) >= qty(5), the order becomes `CONFIRMED` and the
sample's stock drops to 5 — then exits cleanly, no tracebacks. Confirm
`data/samples.json` shows `stock: 5` and `data/orders.json` shows the order
with `status: "CONFIRMED"`. Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire 주문 (승인/거절) into the temporary main menu"
```

## Self-Review Notes

- **Spec coverage:** list (empty/populated), approve (sufficient stock, insufficient stock with correct queue-entry math), reject, invalid-order-id retry, invalid submenu choice — every design-spec behavior has a task and test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `ProductionQueueEntry`'s field names/order match between Task 1 (model) and Task 2/3 (repository, controller usage) exactly; `OrderController`'s constructor now holds `samples`/`orders`/`queue`, all three used consistently in `_approve()`.
