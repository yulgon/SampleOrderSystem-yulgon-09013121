# Phase 7 (Monitoring) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `MonitorController` — 주문량 확인 (order counts by status, `REJECTED` excluded) and 재고량 확인 (per-sample stock vs. outstanding demand, labeled 여유/부족/고갈).

**Architecture:** `MonitorController` holds `SampleRepository` and `OrderRepository`; both menu actions compute their aggregates in memory from `list_all()` — no new repository methods, no caching.

**Tech Stack:** Python 3, pytest (`tmp_path`).

## Global Constraints

- 주문량 확인 shows a count for each of `RESERVED`, `CONFIRMED`, `PRODUCING`, `RELEASE` (0 if none) — `REJECTED` is never counted or shown.
- 재고량 확인's outstanding demand for a sample = sum of `qty` across that sample's `RESERVED` + `PRODUCING` orders only (`CONFIRMED`/`RELEASE`/`REJECTED` orders don't count toward demand).
- Label precedence: `stock == 0` → 고갈 (always, regardless of demand); else `stock >= demand` → 여유; else (`0 < stock < demand`) → 부족.
- Empty-sample-list shows "등록된 시료가 없습니다." for 재고량 확인 (주문량 확인 has no analogous empty state — it always shows all four statuses, just with 0 counts).
- Invalid submenu choice: "잘못된 입력입니다.", re-show the submenu.
- Commit staging: `[RED]` then `[GREEN]`; review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-7-monitoring` — no direct commits to `main`.
- Tests use `tmp_path`.

---

### Task 1: `MonitorController`

**Files:**
- Create: `controller/monitor_controller.py`
- Test: `tests/test_monitor_controller.py`

**Interfaces:**
- Consumes: `FakeView`; `Sample` from `model/sample.py`; `Order`, `OrderStatus` from `model/order.py`; `SampleRepository`, `OrderRepository`
- Produces: `MonitorController(view, base_dir="data")` with `.run() -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitor_controller.py`:

```python
from model.sample import Sample
from model.order import Order, OrderStatus
from controller.monitor_controller import MonitorController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _make_sample(base_dir, name="Sample A", stock=10):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name=name, avg_production_time=2.0, yield_rate=0.9, stock=stock))


def _make_order(base_dir, sample_id, qty=5, status=OrderStatus.RESERVED, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=status))


def test_order_volume_counts_each_status_and_excludes_rejected(tmp_path):
    sample = _make_sample(str(tmp_path))
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.RESERVED)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.CONFIRMED)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.PRODUCING)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.RELEASE)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.REJECTED)

    view = FakeView(inputs=["1", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()

    assert any("RESERVED: 1건" in m for m in view.messages)
    assert any("CONFIRMED: 1건" in m for m in view.messages)
    assert any("PRODUCING: 1건" in m for m in view.messages)
    assert any("RELEASE: 1건" in m for m in view.messages)
    assert not any("REJECTED" in m for m in view.messages)


def test_order_volume_shows_zero_counts_when_no_orders(tmp_path):
    view = FakeView(inputs=["1", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("RESERVED: 0건" in m for m in view.messages)


def test_stock_levels_shows_no_data_message_when_no_samples(tmp_path):
    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert "등록된 시료가 없습니다." in view.messages


def test_stock_levels_shows_surplus_when_stock_covers_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=10)
    _make_order(str(tmp_path), sample.sample_id, qty=5, status=OrderStatus.RESERVED)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("여유" in m for m in view.messages)


def test_stock_levels_shows_shortage_when_stock_below_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=3)
    _make_order(str(tmp_path), sample.sample_id, qty=5, status=OrderStatus.PRODUCING)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("부족" in m for m in view.messages)


def test_stock_levels_shows_depleted_when_stock_is_zero(tmp_path):
    _make_sample(str(tmp_path), stock=0)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("고갈" in m for m in view.messages)


def test_stock_levels_ignores_confirmed_and_release_orders_for_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=5)
    _make_order(str(tmp_path), sample.sample_id, qty=100, status=OrderStatus.CONFIRMED)
    _make_order(str(tmp_path), sample.sample_id, qty=100, status=OrderStatus.RELEASE)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("여유" in m for m in view.messages)


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitor_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller.monitor_controller'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_monitor_controller.py
git commit -m "[RED] add failing tests for MonitorController"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/monitor_controller.py`:

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
                self.view.show_message("잘못된 입력입니다.")

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

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_monitor_controller.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/monitor_controller.py
git commit -m "[GREEN] implement MonitorController"
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
from controller.monitor_controller import MonitorController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)
    production_controller = ProductionController(view)
    release_controller = ReleaseController(view)
    monitor_controller = MonitorController(view)

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
                (6, "모니터링"),
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
        elif choice == "6":
            monitor_controller.run()
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all prior tests plus this phase's Task 1 tests pass (89 + 8 = 97 passed)

- [ ] **Step 3: Manual smoke test — register a low-stock sample, reserve beyond its stock, check both monitoring views, exit**

Before running, trace the exact stdin token sequence against `main.py`'s and each controller's real menu-loop code (this project has repeatedly had off-by-one stdin sequences in prior phases' smoke tests) rather than assuming the sequence below is correct as written — adjust if your trace finds a mismatch, and document what you found either way.

Intended flow: 시료 관리 → register a sample with stock=3 → back to main →
시료 주문 → reserve qty=5 against that sample (creates a shortage: outstanding
demand 5 > stock 3) → back to main → 모니터링 → 주문량 확인 (expect
RESERVED: 1, others 0) → 재고량 확인 (expect 부족 for that sample) → back to
main → exit.

Expected: no tracebacks; 주문량 확인 shows `RESERVED: 1건` and zero for the
other three statuses; 재고량 확인 shows the sample with `상태=부족`. No
`data/` directory should linger afterward — clean up any created during
the smoke test.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire 모니터링 into the temporary main menu"
```

## Self-Review Notes

- **Spec coverage:** 주문량 확인 (per-status counts, REJECTED excluded, zero-order case) and 재고량 확인 (여유/부족/고갈, no-samples case, CONFIRMED/RELEASE excluded from demand) — every design-spec behavior has a test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `MonitorController(view, base_dir="data")` matches how `main.py` (Task 2) instantiates it; `OrderStatus` values used in `VOLUME_STATUSES`/`OUTSTANDING_STATUSES` match `model/order.py`'s actual constants.
