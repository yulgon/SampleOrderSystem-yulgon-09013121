# Phase 6 (Release Processing) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ReleaseController.run()` — prompt an order id, validate it exists and is `CONFIRMED`, transition it to `RELEASE`.

**Architecture:** A new, small `ReleaseController` class (matching `ConsoleMVC`'s PoC shape), holding an `OrderRepository`. Single-pass action, same retry-until-valid helper pattern as `OrderController`'s existing prompts.

**Tech Stack:** Python 3, pytest (`tmp_path`).

## Global Constraints

- Non-numeric order id, missing order, or an order that isn't `CONFIRMED` all show "출고 가능한(CONFIRMED) 주문이 아닙니다." (non-numeric gets "숫자를 입력해주세요.") and re-prompt the SAME field.
- Commit staging: `[RED]` then `[GREEN]`; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-6-release-processing` — no direct commits to `main`.
- Tests use `tmp_path`.

---

### Task 1: `ReleaseController.run()`

**Files:**
- Create: `controller/release_controller.py`
- Test: `tests/test_release_controller.py`

**Interfaces:**
- Consumes: `FakeView`; `Order`, `OrderStatus` from `model/order.py`; `OrderRepository`
- Produces: `ReleaseController(view, base_dir="data")` with `.run() -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_release_controller.py`:

```python
from model.order import Order, OrderStatus
from controller.release_controller import ReleaseController
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _make_order(base_dir, status=OrderStatus.CONFIRMED, sample_id=1, qty=5, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=status))


def test_release_transitions_confirmed_order_to_release(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=[str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert any(f"주문ID={order.order_id}" in m for m in view.messages)


def test_release_retries_on_missing_order_id(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=["999", str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert any("출고 가능한(CONFIRMED) 주문이 아닙니다." in m for m in view.messages)


def test_release_retries_on_non_confirmed_order(tmp_path):
    pending_order = _make_order(str(tmp_path), status=OrderStatus.RESERVED)
    confirmed_order = _make_order(str(tmp_path), status=OrderStatus.CONFIRMED)
    view = FakeView(inputs=[str(pending_order.order_id), str(confirmed_order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(confirmed_order.order_id)
    assert updated.status == OrderStatus.RELEASE


def test_release_retries_on_non_numeric_order_id(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=["abc", str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_release_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller.release_controller'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_release_controller.py
git commit -m "[RED] add failing tests for ReleaseController"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/release_controller.py`:

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
        self.view.show_message(
            f"출고 완료: 주문ID={order.order_id}, 상태={OrderStatus.RELEASE}"
        )

    def _prompt_confirmed_order(self):
        while True:
            raw = self.view.get_input("주문 ID: ")
            try:
                order_id = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.CONFIRMED:
                self.view.show_message("출고 가능한(CONFIRMED) 주문이 아닙니다.")
                continue
            return order
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_release_controller.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/release_controller.py
git commit -m "[GREEN] implement ReleaseController"
```

---

### Task 2: `main.py` wiring + manual smoke test

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
from controller.release_controller import ReleaseController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)
    production_controller = ProductionController(view)
    release_controller = ReleaseController(view)

    while True:
        view.show_menu(
            "메인 메뉴",
            [
                (0, "종료"),
                (1, "시료 관리"),
                (2, "시료 주문"),
                (3, "주문 (승인/거절)"),
                (4, "생산 라인"),
                (5, "출고 처리"),
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
        elif choice == "5":
            release_controller.run()
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1 tests pass (85 + 4 = 89 passed)

- [ ] **Step 3: Manual smoke test — register, reserve, approve (sufficient stock), release, exit**

```bash
mkdir -p data
printf "1\n1\nSample A\n2.0\n0.9\n10\n4\n2\n1\nAcme\n5\n3\n2\n1\n4\n5\n1\n0\n" | python main.py
```

(inputs: 시료관리 → register stock=10 → back → 시료주문 → sample id 1, customer, qty 5 →
주문승인/거절 → 승인 → order id 1 (sufficient stock, becomes CONFIRMED) → back →
출고처리 → order id 1 → exit)

Expected: order goes RESERVED → CONFIRMED (approval, stock 10→5) → RELEASE
(release). No tracebacks. Confirm `data/orders.json` shows the order with
`status: "RELEASE"`. Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire 출고 처리 into the temporary main menu"
```

## Self-Review Notes

- **Spec coverage:** successful release, missing-order-id retry, non-CONFIRMED-order retry, non-numeric-id retry — every design-spec behavior has a test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `ReleaseController(view, base_dir="data")` matches how `main.py` (Task 2) instantiates it.
