# Phase 2 (Sample Management) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 시료 관리 (Sample Management) console menu — register, list, search — backed by Phase 1's `SampleRepository`, with a temporary `main.py` that runs this menu directly for manual smoke testing.

**Architecture:** `view/console_view.py`'s `ConsoleView` does all print/input (same shape as `ConsoleMVC`'s). `controller/sample_controller.py`'s `SampleController` holds the menu loop, constructs `Sample` objects from validated user input, and delegates all persistence to `SampleRepository`. Search filters `SampleRepository.list_all()`'s results in memory — no new repository method.

**Tech Stack:** Python 3, pytest (`tmp_path` for the repository, `capsys` for `ConsoleView`).

## Global Constraints

- Registration prompts for `name`, then `avg_production_time`, `yield_rate`, `stock` in that order. Each numeric field is parsed and validated (matching `Sample`'s own `__post_init__` rules: `avg_production_time > 0`, `0 <= yield_rate <= 1`, `stock >= 0`); on a non-numeric or out-of-range value, re-prompt the SAME field with a message, looping until valid — never fall back to the main menu mid-registration.
- Search is case-sensitive substring match on `name`, computed in-memory over `list_all()` — no new persistence-layer method.
- Invalid main-menu choice: "잘못된 입력입니다.", re-show the menu (existing convention from prior phases/PoCs).
- Empty list/no search matches show a friendly message ("등록된 시료가 없습니다." / "일치하는 시료가 없습니다.") rather than an empty screen.
- Commit staging: every code task's commits are `[RED]` (failing test) then `[GREEN]` (implementation); review-driven fixes are `[REVIEW]`.
- Developed on branch `phase-2-sample-management` — no direct commits to `main`.
- Tests use `tmp_path` for anything touching `SampleRepository` — no test writes to the real `data/` directory.

---

### Task 1: `ConsoleView` + `FakeView` test double

**Files:**
- Create: `view/__init__.py` (empty)
- Create: `view/console_view.py`
- Create: `tests/fakes.py`
- Test: `tests/test_console_view.py`

**Interfaces:**
- Produces: `ConsoleView.show_message(message: str) -> None`
- Produces: `ConsoleView.show_menu(title: str, options: list[tuple[int, str]]) -> None`
- Produces: `ConsoleView.get_input(prompt: str) -> str`
- Produces: `FakeView(inputs: list[str] = None)` with `.messages`, `.menus`, same method signatures as `ConsoleView`, `get_input` pops from `inputs` in order.

- [ ] **Step 1: Write the failing test**

Create `tests/test_console_view.py`:

```python
from view.console_view import ConsoleView


def test_show_menu_prints_title_and_numbered_options(capsys):
    view = ConsoleView()
    view.show_menu("시료 관리", [(1, "시료 등록"), (2, "시료 조회"), (3, "시료 검색"), (4, "돌아가기")])
    captured = capsys.readouterr()
    assert "시료 관리" in captured.out
    assert "1. 시료 등록" in captured.out
    assert "4. 돌아가기" in captured.out


def test_show_message_prints_the_message(capsys):
    view = ConsoleView()
    view.show_message("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_console_view.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'view'`

- [ ] **Step 3: Commit the failing test**

Create `view/__init__.py` — empty file.

```bash
git add view/__init__.py tests/test_console_view.py
git commit -m "[RED] add failing tests for ConsoleView"
```

- [ ] **Step 4: Write minimal implementation**

Create `view/console_view.py`:

```python
class ConsoleView:
    def show_message(self, message):
        print(message)

    def show_menu(self, title, options):
        print(f"\n=== {title} ===")
        for number, label in options:
            print(f"{number}. {label}")

    def get_input(self, prompt):
        return input(prompt)
```

Create `tests/fakes.py`:

```python
class FakeView:
    """Test double for ConsoleView: feeds canned inputs, records shown output."""

    def __init__(self, inputs=None):
        self._inputs = list(inputs or [])
        self.messages = []
        self.menus = []

    def show_message(self, message):
        self.messages.append(message)

    def show_menu(self, title, options):
        self.menus.append((title, options))

    def get_input(self, prompt):
        return self._inputs.pop(0)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_console_view.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add view/console_view.py tests/fakes.py
git commit -m "[GREEN] implement ConsoleView and FakeView test double"
```

---

### Task 2: `SampleController` (register / list / search)

**Files:**
- Create: `controller/__init__.py` (empty)
- Create: `controller/sample_controller.py`
- Test: `tests/test_sample_controller.py`

**Interfaces:**
- Consumes: `FakeView` from `tests/fakes.py`; `Sample` from `model/sample.py`; `SampleRepository` from `persistence/sample_repository.py`
- Produces: `SampleController(view, base_dir="data")` with `.run() -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_sample_controller.py`:

```python
from model.sample import Sample
from controller.sample_controller import SampleController
from persistence.sample_repository import SampleRepository
from tests.fakes import FakeView


def test_register_creates_sample_and_shows_assigned_id(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert len(samples) == 1
    assert samples[0].name == "Sample A"
    assert any("ID=1" in m for m in view.messages)


def test_register_retries_on_non_numeric_avg_production_time(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "abc", "2.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].avg_production_time == 2.5
    assert any("숫자를 입력해주세요" in m for m in view.messages)


def test_register_retries_on_out_of_range_yield_rate(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "1.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].yield_rate == 0.9


def test_register_retries_on_negative_stock(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "0.9", "-1", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].stock == 10


def test_list_shows_no_data_message_when_empty(tmp_path):
    view = FakeView(inputs=["2", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "등록된 시료가 없습니다." in view.messages


def test_list_shows_registered_samples(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))

    view = FakeView(inputs=["2", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("Sample A" in m for m in view.messages)


def test_search_finds_matching_sample_only(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))
    repo.create(Sample(name="Other B", avg_production_time=1.0, yield_rate=0.8, stock=5))

    view = FakeView(inputs=["3", "Sample", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("Sample A" in m for m in view.messages)
    assert not any("Other B" in m for m in view.messages)


def test_search_shows_no_match_message(tmp_path):
    view = FakeView(inputs=["3", "Nonexistent", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "일치하는 시료가 없습니다." in view.messages


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sample_controller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'controller'`

- [ ] **Step 3: Commit the failing test**

Create `controller/__init__.py` — empty file.

```bash
git add controller/__init__.py tests/test_sample_controller.py
git commit -m "[RED] add failing tests for SampleController"
```

- [ ] **Step 4: Write minimal implementation**

Create `controller/sample_controller.py`:

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
                self.view.show_message("잘못된 입력입니다.")

    def _prompt_float(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = float(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_message(error_message)
                continue
            return value

    def _prompt_int(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_message(error_message)
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
            "수율은 0~1 사이여야 합니다.",
            lambda v: 0 <= v <= 1,
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
        self.view.show_message(
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

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_sample_controller.py -v`
Expected: 9 passed

- [ ] **Step 6: Commit the implementation**

```bash
git add controller/sample_controller.py
git commit -m "[GREEN] implement SampleController with register/list/search"
```

---

### Task 3: `main.py` wiring + full test suite + manual smoke test

**Files:**
- Create: `main.py`

**Interfaces:**
- Consumes: `ConsoleView` from `view/console_view.py`; `SampleController` from `controller/sample_controller.py`
- Produces: `main()` entry point run via `if __name__ == "__main__"`

**No new tests** — this task is integration wiring, verified by the existing suite plus a manual smoke test.

- [ ] **Step 1: Write main.py**

Create `main.py`:

```python
from view.console_view import ConsoleView
from controller.sample_controller import SampleController


def main():
    view = ConsoleView()
    controller = SampleController(view)
    controller.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full automated test suite**

Run: `pytest -v`
Expected: all tests from Phase 1 plus this phase's Task 1-2 tests pass (40 + 2 + 9 = 51 passed)

- [ ] **Step 3: Manual smoke test — register, list, search, exit**

```bash
mkdir -p data
printf "1\nSample A\n2.5\n0.9\n10\n2\n3\nSample\n4\n" | python main.py
```

(inputs: register → name/avg/yield/stock → list → search "Sample" → exit)

Expected: prints the 시료 관리 menu, registration confirmation with `ID=1`, the listed sample, the search match, then exits — no tracebacks. Confirm `data/samples.json` has one record. Clean up afterward:

```bash
rm -rf data
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "[GREEN] wire up main.py entry point for Phase 2 manual testing"
```

## Self-Review Notes

- **Spec coverage:** register (with per-field retry for non-numeric and validation-failure cases), list (empty and populated), search (match, no-match), invalid menu choice — every design-spec behavior has a task and test.
- **Placeholder scan:** no TBD/TODO; every step has complete, runnable code.
- **Type consistency:** `SampleController(view, base_dir="data")`'s constructor matches how `main.py` (Task 3) instantiates it; `FakeView`'s method names match `ConsoleView`'s exactly (established Task 1, relied on unchanged in Task 2).
