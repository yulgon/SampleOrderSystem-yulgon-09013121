# Phase 10 — Console UI Styling — Design

## Context

The core 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`) is complete
and verified (Phase 9). This is an additional phase, requested after the
fact: make the console UI more visually appealing — colored text and a
program-name banner — without adding any external dependency (this
project has used stdlib only through all 9 phases).

## Scope

**In scope:** ANSI color codes in `ConsoleView` (ASCII banner, colored
menu titles/status bar, green success messages, red error messages),
routing the existing 6 controllers' error/success `show_message(...)`
calls to new `show_error(...)`/`show_success(...)` methods, and a
Windows-console ANSI-enable step (stdlib `ctypes` only — no `colorama`).

**Out of scope:** any new business logic, any new menu, any new
dependency. This is a pure presentation-layer change.

## Color Scheme

- Banner (프로그램명): bold cyan.
- Menu titles (`show_menu`) and the status bar (`show_status_bar`): cyan.
- Success messages (`show_success`): green.
- Error messages (`show_error`): red.
- Plain informational output (`show_message` — e.g. list/search results,
  "no data" notices): uncolored, unchanged.

## `ConsoleView` Changes

```python
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"


class ConsoleView:
    def __init__(self):
        _enable_windows_ansi()

    def show_message(self, message):
        print(message)  # unchanged

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

`_enable_windows_ansi()` (module-level helper): on `sys.platform ==
"win32"`, uses `ctypes` to read the console's current output mode via
`GetConsoleMode` and OR in `ENABLE_VIRTUAL_TERMINAL_PROCESSING` (0x0004)
via `SetConsoleMode`, so ANSI codes render as color instead of literal
escape-sequence garbage on Windows terminals that don't already have it
enabled. No-op on non-Windows platforms.

## Controller Changes

Each of the 6 controllers' existing `self.view.show_message(...)` calls
are re-routed by message *intent*, not reworded:
- Validation/lookup errors ("잘못된 입력입니다.", "숫자를 입력해주세요.",
  "존재하지 않는 시료 ID입니다.", "유효한 접수 주문이 아닙니다.", etc.) →
  `self.view.show_error(...)`.
- Completion/success confirmations ("시료 등록 완료: ...", "주문 접수
  완료: ...", "승인 완료 (재고 차감): ...", "재고 부족 - 생산 등록: ...",
  "주문 거절 완료: ...", "생산 완료 처리: ...", "출고 완료: ...") →
  `self.view.show_success(...)`.
- Plain informational/listing output (샘플 목록, 검색 결과, "등록된 시료가
  없습니다." style empty-state notices, 모니터링's counts/labels) stays on
  `show_message(...)` — these aren't errors or successes, just data.

No message text changes — only which view method delivers each one.

## `main.py`

Calls `view.show_banner()` once, before constructing the controllers and
calling `app.run()`.

## Test Compatibility (key design decision)

`tests/fakes.py`'s `FakeView` gets `show_error`/`show_success` methods
that append to the *same* `self.messages` list `show_message` already
uses:

```python
    def show_error(self, message):
        self.messages.append(message)

    def show_success(self, message):
        self.messages.append(message)
```

Since every existing controller test asserts on message *content*
(`"...입니다." in view.messages`), not which method delivered it, **zero
existing tests need to change** when the 6 controllers switch from
`show_message` to `show_error`/`show_success` for the same strings. Visual
styling correctness is verified separately, at the `ConsoleView` level
only (new tests, see below) — this keeps the styling change a pure
additive/routing change with no risk to the 106 tests already proving
business-logic correctness.

## Testing

New `capsys`-based tests for `ConsoleView.show_success`,
`ConsoleView.show_error`, and `ConsoleView.show_banner` confirming each
wraps its output in the correct ANSI color codes (and that
`show_menu`/`show_status_bar` still contain the cyan code alongside their
existing content). The full pre-existing 106-test suite must still pass
unchanged after the 6 controllers are re-routed. A manual check in an
actual terminal confirms colors render (not just that the escape codes
are present in captured stdout, which `capsys` can verify but a human eye
in a real terminal is the actual acceptance bar for "looks good").

## Process Note

Same convention as prior phases: `[RED]`/`[GREEN]`/`[REVIEW]` commit
staging, developed on branch `phase-10-console-ui-styling`, merged via a
PR the user reviews and merges manually.
