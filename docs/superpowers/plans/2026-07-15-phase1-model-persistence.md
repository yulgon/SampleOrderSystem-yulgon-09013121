# Phase 1 (Model + Persistence) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build real `Sample`/`Order` dataclasses (with `to_dict`/`from_dict` and minimal validation) and a working JSON persistence layer underneath them — a generic `JsonRepository` plus typed `SampleRepository`/`OrderRepository` wrappers — with system-assigned sequential ids. No console UI yet.

**Architecture:** `model/` holds pure dataclasses that know how to serialize themselves; `persistence/repository.py` is a fully generic dict-based CRUD store (max+1 ids); `persistence/sample_repository.py` and `persistence/order_repository.py` are thin typed wrappers that convert between dataclasses and the generic repository's dicts. No layer knows about the others' internals beyond this.

**Tech Stack:** Python 3, pytest (`tmp_path` for filesystem isolation), stdlib `json`/`os`/`dataclasses` only.

## Global Constraints

- No console UI, no business logic (stock deduction, status transitions beyond storing a value, production scheduling) — this phase is data foundation only.
- IDs are sequential integers via `max(existing ids, default=0) + 1` — identical scheme to the `DataPersistence` PoC stage.
- `JsonRepository.get`/`update`/`delete` against a missing id return `None`/`None`/`False` — never raise for "not found".
- `Sample`/`Order` validate minimally in `__post_init__` (see design spec) and raise `ValueError` on violation — no other validation.
- **Commit staging:** every task below produces exactly two commits — `[RED] ...` (the failing test, committed as-is even though it fails) then `[GREEN] ...` (the minimal implementation that makes it pass). If a task reviewer finds issues, the fix is a third commit prefixed `[REVIEW] ...`.
- This is developed on branch `phase-1-model-persistence` — no direct commits to `main`; a PR is opened when the phase is done.
- Tests use pytest's `tmp_path` fixture for anything touching `persistence/` — no test ever writes to the real `data/` directory.
- Verify tests with `pytest -v` (or a focused `pytest path/to/test_file.py -v`) after every implementation step.

---

### Task 1: `Sample` dataclass

**Files:**
- Create: `conftest.py` (repo root, empty — makes `model`/`persistence` importable from `tests/`)
- Create: `pytest.ini`
- Create: `model/__init__.py` (empty)
- Create: `model/sample.py`
- Test: `tests/test_sample.py`

**Interfaces:**
- Produces: `Sample(name, avg_production_time, yield_rate, stock, sample_id=None)` dataclass
- Produces: `Sample.to_dict() -> dict` (includes `"id"` key only when `sample_id is not None`)
- Produces: `Sample.from_dict(data: dict) -> Sample` (classmethod; reads `data.get("id")` into `sample_id`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_sample.py`:

```python
import pytest

from model.sample import Sample


def test_to_dict_includes_id_when_present():
    sample = Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10, sample_id=1)
    assert sample.to_dict() == {
        "id": 1,
        "name": "Sample A",
        "avg_production_time": 2.5,
        "yield_rate": 0.9,
        "stock": 10,
    }


def test_to_dict_omits_id_when_none():
    sample = Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10)
    assert "id" not in sample.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "name": "Sample A", "avg_production_time": 2.5, "yield_rate": 0.9, "stock": 10}
    sample = Sample.from_dict(data)
    assert sample.sample_id == 1
    assert sample.name == "Sample A"
    assert sample.to_dict() == data


def test_raises_on_non_positive_avg_production_time():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=0, yield_rate=0.9, stock=10)


def test_raises_on_out_of_range_yield_rate():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=2.0, yield_rate=1.5, stock=10)


def test_raises_on_negative_stock():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=2.0, yield_rate=0.9, stock=-1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sample.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'model'`

- [ ] **Step 3: Commit the failing test**

Create `conftest.py` (repo root) — empty file. Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
```

Create `model/__init__.py` — empty file, and an empty `model/sample.py` (just enough to make imports resolve to a clearer failure, or leave `model/sample.py` absent if that's cleaner — either way `tests/test_sample.py` must fail on `Sample` being undefined/missing, not on a resolvable import). Commit:

```bash
git add conftest.py pytest.ini model/__init__.py tests/test_sample.py
git commit -m "[RED] add failing tests for Sample dataclass"
```

- [ ] **Step 4: Write minimal implementation**

Create/overwrite `model/sample.py`:

```python
from dataclasses import dataclass


@dataclass
class Sample:
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int
    sample_id: int = None

    def __post_init__(self):
        if self.avg_production_time <= 0:
            raise ValueError("avg_production_time must be positive")
        if not (0 <= self.yield_rate <= 1):
            raise ValueError("yield_rate must be between 0 and 1")
        if self.stock < 0:
            raise ValueError("stock must not be negative")

    def to_dict(self):
        data = {
            "name": self.name,
            "avg_production_time": self.avg_production_time,
            "yield_rate": self.yield_rate,
            "stock": self.stock,
        }
        if self.sample_id is not None:
            data["id"] = self.sample_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            avg_production_time=data["avg_production_time"],
            yield_rate=data["yield_rate"],
            stock=data["stock"],
            sample_id=data.get("id"),
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_sample.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add model/sample.py
git commit -m "[GREEN] implement Sample dataclass with to_dict/from_dict and validation"
```

---

### Task 2: `Order` dataclass + `OrderStatus`

**Files:**
- Create: `model/order.py`
- Test: `tests/test_order.py`

**Interfaces:**
- Produces: `OrderStatus` with class attributes `RESERVED`, `REJECTED`, `PRODUCING`, `CONFIRMED`, `RELEASE` (each equal to its own name) and `OrderStatus.ALL` (tuple of all 5)
- Produces: `Order(sample_id, customer, qty, status, order_id=None)` dataclass
- Produces: `Order.to_dict() -> dict` / `Order.from_dict(data) -> Order` (same pattern as `Sample`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_order.py`:

```python
import pytest

from model.order import Order, OrderStatus


def test_order_status_values():
    assert OrderStatus.RESERVED == "RESERVED"
    assert OrderStatus.REJECTED == "REJECTED"
    assert OrderStatus.PRODUCING == "PRODUCING"
    assert OrderStatus.CONFIRMED == "CONFIRMED"
    assert OrderStatus.RELEASE == "RELEASE"
    assert set(OrderStatus.ALL) == {"RESERVED", "REJECTED", "PRODUCING", "CONFIRMED", "RELEASE"}


def test_to_dict_includes_id_when_present():
    order = Order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED, order_id=1)
    assert order.to_dict() == {
        "id": 1,
        "sample_id": 1,
        "customer": "Acme",
        "qty": 5,
        "status": "RESERVED",
    }


def test_to_dict_omits_id_when_none():
    order = Order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED)
    assert "id" not in order.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "sample_id": 1, "customer": "Acme", "qty": 5, "status": "RESERVED"}
    order = Order.from_dict(data)
    assert order.order_id == 1
    assert order.to_dict() == data


def test_raises_on_non_positive_qty():
    with pytest.raises(ValueError):
        Order(sample_id=1, customer="Acme", qty=0, status=OrderStatus.RESERVED)


def test_raises_on_invalid_status():
    with pytest.raises(ValueError):
        Order(sample_id=1, customer="Acme", qty=5, status="NOT_A_STATUS")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_order.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'model.order'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_order.py
git commit -m "[RED] add failing tests for Order dataclass and OrderStatus"
```

- [ ] **Step 4: Write minimal implementation**

Create `model/order.py`:

```python
from dataclasses import dataclass


class OrderStatus:
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"

    ALL = (RESERVED, REJECTED, PRODUCING, CONFIRMED, RELEASE)


@dataclass
class Order:
    sample_id: int
    customer: str
    qty: int
    status: str
    order_id: int = None

    def __post_init__(self):
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.status not in OrderStatus.ALL:
            raise ValueError(f"invalid status: {self.status}")

    def to_dict(self):
        data = {
            "sample_id": self.sample_id,
            "customer": self.customer,
            "qty": self.qty,
            "status": self.status,
        }
        if self.order_id is not None:
            data["id"] = self.order_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            sample_id=data["sample_id"],
            customer=data["customer"],
            qty=data["qty"],
            status=data["status"],
            order_id=data.get("id"),
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_order.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add model/order.py
git commit -m "[GREEN] implement Order dataclass, OrderStatus, and validation"
```

---

### Task 3: Generic `JsonRepository`

**Files:**
- Create: `persistence/__init__.py` (empty)
- Create: `persistence/repository.py`
- Test: `tests/test_repository.py`

**Interfaces:**
- Produces: `JsonRepository(collection_name, base_dir="data")`
- Produces: `.list_all() -> list[dict]`
- Produces: `.get(record_id: int) -> dict | None`
- Produces: `.create(data: dict) -> dict` (assigns `id` via max+1, persists, returns full record)
- Produces: `.update(record_id: int, data: dict) -> dict | None` (merges fields, preserves id, `None` if missing)
- Produces: `.delete(record_id: int) -> bool`

- [ ] **Step 1: Write the failing test**

Create `tests/test_repository.py`:

```python
from persistence.repository import JsonRepository


def test_create_assigns_sequential_id_and_returns_record(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    record = repo.create({"name": "Sample A"})
    assert record["id"] == 1

    second = repo.create({"name": "Sample B"})
    assert second["id"] == 2


def test_get_returns_matching_record(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    created = repo.create({"name": "Sample A"})
    assert repo.get(created["id"]) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_records(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    repo.create({"name": "Sample B"})
    assert repo.list_all() == [
        {"id": 1, "name": "Sample A"},
        {"id": 2, "name": "Sample B"},
    ]


def test_list_all_returns_empty_list_when_no_file_exists(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.list_all() == []


def test_create_persists_across_repository_instances(tmp_path):
    repo1 = JsonRepository("samples", base_dir=str(tmp_path))
    repo1.create({"name": "Sample A"})
    repo2 = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo2.list_all() == [{"id": 1, "name": "Sample A"}]


def test_update_merges_fields_and_persists(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A", "stock": 10})
    updated = repo.update(1, {"stock": 20})
    assert updated == {"id": 1, "name": "Sample A", "stock": 20}
    assert repo.get(1) == {"id": 1, "name": "Sample A", "stock": 20}


def test_update_returns_none_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.update(999, {"stock": 20}) is None


def test_delete_removes_record_and_returns_true(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    assert repo.delete(1) is True
    assert repo.get(1) is None
    assert repo.list_all() == []


def test_delete_returns_false_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    assert repo.delete(999) is False
    assert repo.list_all() == [{"id": 1, "name": "Sample A"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'persistence'`

- [ ] **Step 3: Commit the failing test**

```bash
git add persistence/__init__.py tests/test_repository.py
git commit -m "[RED] add failing tests for JsonRepository"
```

- [ ] **Step 4: Write minimal implementation**

Create `persistence/repository.py`:

```python
import json
import os


class JsonRepository:
    def __init__(self, collection_name, base_dir="data"):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, f"{collection_name}.json")

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, records):
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._load()

    def get(self, record_id):
        for record in self._load():
            if record["id"] == record_id:
                return record
        return None

    def create(self, data):
        records = self._load()
        next_id = max((r["id"] for r in records), default=0) + 1
        record = {"id": next_id, **data}
        records.append(record)
        self._save(records)
        return record

    def update(self, record_id, data):
        records = self._load()
        for i, r in enumerate(records):
            if r["id"] == record_id:
                updated = {**r, **data, "id": record_id}
                records[i] = updated
                self._save(records)
                return updated
        return None

    def delete(self, record_id):
        records = self._load()
        for i, r in enumerate(records):
            if r["id"] == record_id:
                del records[i]
                self._save(records)
                return True
        return False
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_repository.py -v`
Expected: 10 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add persistence/repository.py
git commit -m "[GREEN] implement JsonRepository with full CRUD and max+1 ids"
```

---

### Task 4: `SampleRepository`

**Files:**
- Create: `persistence/sample_repository.py`
- Test: `tests/test_sample_repository.py`

**Interfaces:**
- Consumes: `Sample` from `model/sample.py`; `JsonRepository` from `persistence/repository.py`
- Produces: `SampleRepository(base_dir="data")` with `.create(sample: Sample) -> Sample`, `.get(sample_id) -> Sample | None`, `.list_all() -> list[Sample]`, `.update(sample_id, changes: dict) -> Sample | None`, `.delete(sample_id) -> bool`

- [ ] **Step 1: Write the failing test**

Create `tests/test_sample_repository.py`:

```python
from model.sample import Sample
from persistence.sample_repository import SampleRepository


def _make_sample(name="Sample A", stock=10):
    return Sample(name=name, avg_production_time=2.5, yield_rate=0.9, stock=stock)


def test_create_returns_sample_with_assigned_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert isinstance(created, Sample)
    assert created.sample_id == 1
    assert created.name == "Sample A"


def test_get_returns_matching_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert repo.get(created.sample_id) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_samples_in_order(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(_make_sample(name="A"))
    repo.create(_make_sample(name="B"))
    assert [s.name for s in repo.list_all()] == ["A", "B"]


def test_update_merges_fields_and_returns_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample(stock=5))
    updated = repo.update(created.sample_id, {"stock": 20})
    assert updated.stock == 20
    assert updated.name == "Sample A"


def test_update_returns_none_for_missing_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    assert repo.update(999, {"stock": 20}) is None


def test_delete_removes_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert repo.delete(created.sample_id) is True
    assert repo.get(created.sample_id) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sample_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'persistence.sample_repository'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_sample_repository.py
git commit -m "[RED] add failing tests for SampleRepository"
```

- [ ] **Step 4: Write minimal implementation**

Create `persistence/sample_repository.py`:

```python
from model.sample import Sample
from persistence.repository import JsonRepository


class SampleRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("samples", base_dir=base_dir)

    def create(self, sample):
        record = self._repo.create(sample.to_dict())
        return Sample.from_dict(record)

    def get(self, sample_id):
        record = self._repo.get(sample_id)
        return Sample.from_dict(record) if record else None

    def list_all(self):
        return [Sample.from_dict(record) for record in self._repo.list_all()]

    def update(self, sample_id, changes):
        record = self._repo.update(sample_id, changes)
        return Sample.from_dict(record) if record else None

    def delete(self, sample_id):
        return self._repo.delete(sample_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_sample_repository.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add persistence/sample_repository.py
git commit -m "[GREEN] implement SampleRepository wrapping JsonRepository"
```

---

### Task 5: `OrderRepository`

**Files:**
- Create: `persistence/order_repository.py`
- Test: `tests/test_order_repository.py`

**Interfaces:**
- Consumes: `Order`, `OrderStatus` from `model/order.py`; `JsonRepository` from `persistence/repository.py`
- Produces: `OrderRepository(base_dir="data")` with `.create(order: Order) -> Order`, `.get(order_id) -> Order | None`, `.list_all() -> list[Order]`, `.update(order_id, changes: dict) -> Order | None`, `.delete(order_id) -> bool`

- [ ] **Step 1: Write the failing test**

Create `tests/test_order_repository.py`:

```python
from model.order import Order, OrderStatus
from persistence.order_repository import OrderRepository


def _make_order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED):
    return Order(sample_id=sample_id, customer=customer, qty=qty, status=status)


def test_create_returns_order_with_assigned_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert isinstance(created, Order)
    assert created.order_id == 1
    assert created.status == OrderStatus.RESERVED


def test_get_returns_matching_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert repo.get(created.order_id) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_orders_in_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    repo.create(_make_order(customer="Acme"))
    repo.create(_make_order(customer="Globex"))
    assert [o.customer for o in repo.list_all()] == ["Acme", "Globex"]


def test_update_changes_status_and_returns_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    updated = repo.update(created.order_id, {"status": OrderStatus.CONFIRMED})
    assert updated.status == OrderStatus.CONFIRMED
    assert updated.customer == "Acme"


def test_update_returns_none_for_missing_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    assert repo.update(999, {"status": OrderStatus.REJECTED}) is None


def test_delete_removes_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert repo.delete(created.order_id) is True
    assert repo.get(created.order_id) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_order_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'persistence.order_repository'`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_order_repository.py
git commit -m "[RED] add failing tests for OrderRepository"
```

- [ ] **Step 4: Write minimal implementation**

Create `persistence/order_repository.py`:

```python
from model.order import Order
from persistence.repository import JsonRepository


class OrderRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("orders", base_dir=base_dir)

    def create(self, order):
        record = self._repo.create(order.to_dict())
        return Order.from_dict(record)

    def get(self, order_id):
        record = self._repo.get(order_id)
        return Order.from_dict(record) if record else None

    def list_all(self):
        return [Order.from_dict(record) for record in self._repo.list_all()]

    def update(self, order_id, changes):
        record = self._repo.update(order_id, changes)
        return Order.from_dict(record) if record else None

    def delete(self, order_id):
        return self._repo.delete(order_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_order_repository.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add persistence/order_repository.py
git commit -m "[GREEN] implement OrderRepository wrapping JsonRepository"
```

---

### Task 6: Full suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `pytest -v`
Expected: 36 passed (6 Sample + 6 Order + 10 JsonRepository + 7 SampleRepository + 7 OrderRepository)

- [ ] **Step 2: Confirm no stray artifacts**

Run: `git status` — expect a clean working tree (no uncommitted files, no `data/` directory lingering from test runs, since all tests use `tmp_path`).

No commit for this task — it's a verification checkpoint before opening the PR.

## Self-Review Notes

- **Spec coverage:** `Sample`/`Order` dataclasses with validation (Task 1-2), generic `JsonRepository` (Task 3), typed wrappers (Task 4-5) — every deliverable in the design spec has a task.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `SampleRepository`/`OrderRepository` both call `JsonRepository(collection_name, base_dir=base_dir)` the same way; `Sample.from_dict`/`to_dict` and `Order.from_dict`/`to_dict` follow an identical shape (id-inclusion-when-present pattern), so the two wrappers are structurally parallel.
- **Commit staging:** every task follows the `[RED]` → `[GREEN]` two-commit pattern per the new convention; Task 6 is verification-only with no commit.
