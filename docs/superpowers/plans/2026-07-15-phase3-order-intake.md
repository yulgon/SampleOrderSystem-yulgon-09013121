# Phase 3 (Order Intake) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `OrderController.run_reserve()` — the 시료 예약 flow: collect an existing sample id, customer, and quantity, then create an `Order` with status `RESERVED` via `OrderRepository`. Wire a temporary main menu that reaches both Phase 2's 시료 관리 and this phase's 시료 주문.

**Architecture:** `controller/order_controller.py`'s `OrderController` holds `SampleRepository` (to validate the referenced sample exists) and `OrderRepository` (to persist the new order). `run_reserve()` is a single-pass action (no submenu loop) — matching PRD §6.2 and the reused `ConsoleMVC` shape. `main.py` gets a small inline menu loop (not a class — it's explicitly temporary, replaced by a real `AppController` in Phase 8).

**Tech Stack:** Python 3, pytest (`tmp_path` for repository-backed tests).

## Global Constraints

- `run_reserve()` prompts 시료 ID first; a non-numeric or non-existent id re-prompts the SAME field ("숫자를 입력해주세요." / "존재하지 않는 시료 ID입니다.") — never bounces to a higher menu.
- Then prompts 고객명 (no validation, same as Phase 2's sample name field).
- Then prompts 주문 수량; non-numeric or non-positive re-prompts the SAME field ("숫자를 입력해주세요." / "주문 수량은 0보다 커야 합니다.").
- The created `Order` always has `status=OrderStatus.RESERVED`.
- No approval/rejection logic in this phase — that's Phase 4, added to the same `OrderController` class later.
- Commit staging: `[RED]` (failing test) then `[GREEN]` (implementation); review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-3-order-intake` — no direct commits to `main`.
- Tests use `tmp_path` for anything touching `SampleRepository`/`OrderRepository`.

---

### Task 1: `OrderController.run_reserve()`

**Files:**
- Create: `controller/order_controller.py`
- Test: `tests/test_order_controller.py`

**Interfaces:**
- Consumes: `FakeView` from `tests/fakes.py`; `Sample` from `model/sample.py`; `Order`, `OrderStatus` from `model/order.py`; `SampleRepository` from `persistence/sample_repository.py`; `OrderRepository` from `persistence/order_repository.py`
- Produces: `OrderController(view, base_dir="data")` with `.run_reserve() -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_order_controller.py`:

```python
from model.sample import Sample
from model.order import OrderStatus
from controller.order_controller import OrderController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _register_sample(base_dir):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))


def test_run_reserve_creates_order_with_reserved_status(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1
    assert orders[0].sample_id == sample.sample_id
    assert orders[0].customer == "Acme"
    assert orders[0].qty == 5
    assert orders[0].status == OrderStatus.RESERVED
    assert any("ID=1" in m for m in view.messages)


def test_run_reserve_retries_on_missing_sample_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=["999", str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1
    assert orders[0].sample_id == sample.sample_id
    assert any("존재하지 않는 시료 ID입니다." in m for m in view.messages)


def test_run_reserve_retries_on_non_numeric_sample_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=["abc", str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1


def test_run_reserve_retries_on_non_numeric_qty(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "abc", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert orders[0].qty == 5


def test_run_reserve_retries_on_non_positive_qty(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "0", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert orders[0].qty == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_order_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller.order_controller'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_order_controller.py
git commit -m "[RED] add failing tests for OrderController.run_reserve()"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/order_controller.py`:

```python
from model.order import Order, OrderStatus
from persistence.order_repository import OrderRepository
from persistence.sample_repository import SampleRepository


class OrderController:
    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)

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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_order_controller.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/order_controller.py
git commit -m "[GREEN] implement OrderController.run_reserve()"
```

---

### Task 2: Temporary main menu + manual smoke test

**Files:**
- Modify: `main.py`

**Interfaces:**
- Consumes: `ConsoleView`, `SampleController`, `OrderController`

**No new tests** — this task is integration wiring, verified by the existing suite plus a manual smoke test.

- [ ] **Step 1: Rewrite main.py**

Replace `main.py`'s contents with:

```python
from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)

    while True:
        view.show_menu("메인 메뉴", [(0, "종료"), (1, "시료 관리"), (2, "시료 주문")])
        choice = view.get_input("메뉴 번호를 입력하세요: ")

        if choice == "0":
            return
        elif choice == "1":
            sample_controller.run()
        elif choice == "2":
            order_controller.run_reserve()
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1 tests pass (51 + 5 = 56 passed)

- [ ] **Step 3: Manual smoke test — register a sample, then reserve an order against it, then exit**

```bash
mkdir -p data
printf "1\n1\nSample A\n2.5\n0.9\n10\n4\n2\n1\nAcme\n5\n0\n" | python main.py
```

(inputs: 시료 관리 → register → name/avg/yield/stock → back to sample menu → 시료 주문 → sample id 1 → customer → qty 5 → exit)

Expected: prints the main menu, walks into 시료 관리 to register one sample, returns, walks into 시료 주문 to reserve one order against sample id 1, then exits cleanly — no tracebacks. Confirm `data/orders.json` has one record with `status: "RESERVED"`. Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire temporary main menu reaching Sample Management and Order Intake"
```

## Self-Review Notes

- **Spec coverage:** happy-path reservation, missing-sample-id retry, non-numeric-sample-id retry, non-numeric-qty retry, non-positive-qty retry — every design-spec behavior has a test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `OrderController(view, base_dir="data")` matches how `main.py` (Task 2) instantiates it; `Order(sample_id=..., customer=..., qty=..., status=OrderStatus.RESERVED)` matches `model/order.py`'s real constructor signature exactly.
