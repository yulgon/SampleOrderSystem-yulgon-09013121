# Phase 2 — Sample Management Menu — Design

## Context

This is Phase 2 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`).
Phase 1 built real `Sample`/`Order` dataclasses and the JSON persistence
layer (`SampleRepository`/`OrderRepository` over a generic `JsonRepository`).
This phase builds the first real console menu — 시료 관리 (Sample
Management) — replacing `ConsoleMVC`'s echo-only PoC stub with genuine
persistence-backed behavior, per PRD.md §6.1.

## Scope

**In scope:** 시료 등록 (register), 시료 조회 (list), 시료 검색 (search) —
all backed by Phase 1's `SampleRepository`. A minimal `main.py` that runs
just this menu directly, for manual smoke testing (no `AppController`/main
menu yet — that's Phase 8).

**Out of scope:** every other menu (order intake, approval, production,
release, monitoring, status bar) — those are later phases. No search
method added to `SampleRepository` — search is done in-memory in the
controller over `list_all()`'s results.

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  main.py                     # temporary: runs SampleController directly
  view/
    __init__.py
    console_view.py            # ConsoleView (same pattern as ConsoleMVC)
  controller/
    __init__.py
    sample_controller.py        # 시료 관리 menu, wired to SampleRepository
```

`main.py`'s content here is explicitly temporary — Phase 8 replaces it with
one that wires an `AppController` across every controller from every phase.

## Menu Flow

```
시료 관리: 1. 시료 등록   2. 시료 조회   3. 시료 검색   4. 돌아가기

1 -> prompt name, avg_production_time, yield_rate, stock in order.
     Each numeric field is parsed and validated (via Sample's own
     __post_init__); on parse failure or ValueError, re-prompt the SAME
     field until a valid value is given — no field is skipped, no return
     to the menu on a bad value.
     On success: SampleRepository.create(...) -> show the assigned id and
     entered fields.
2 -> SampleRepository.list_all() -> print every sample (id, name,
     avg_production_time, yield_rate, stock). If empty, show
     "등록된 시료가 없습니다."
3 -> prompt a search keyword -> filter list_all()'s results in-memory for
     samples whose name contains the keyword (case-sensitive substring
     match) -> print matches, or "일치하는 시료가 없습니다." if none.
4 -> return to caller (there is no higher menu yet in this phase's
     main.py — returning exits the program)
```

## Error Handling

Invalid main-menu choice: "잘못된 입력입니다.", re-show the menu (existing
convention). Invalid numeric input during registration (non-numeric, or
numeric but violating `Sample`'s validation — e.g. negative stock,
out-of-range yield_rate): re-prompt the same field with a message
indicating the problem, looping until a valid value is entered — the user
is never bounced back to the main menu mid-registration.

## Testing

`ConsoleView` tested via `capsys` (same as `ConsoleMVC`/`DataMonitor`).
`SampleController` tested with a `FakeView` (new for this repo, same shape
as prior stages' fakes) driving canned inputs, backed by a real
`SampleRepository` over `tmp_path` — so tests verify actual persistence
(a registered sample really lands in the JSON file, `list_all`/search
really reflect it), not just that certain messages were shown. Covered
cases: successful registration; non-numeric retry loop; validation-failure
retry loop (e.g. negative stock, invalid yield_rate); list with data and
with none; search with a match, a partial match, and no match; invalid
menu choice.

## Process Note

Same convention as Phase 1: `[RED]`/`[GREEN]`/`[REVIEW]` commit staging,
developed on branch `phase-2-sample-management`, merged via a PR the user
reviews and merges manually.
