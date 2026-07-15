# SampleOrderSystem

## What this is

`SampleOrderSystem` is the final, real (non-PoC) program in a 5-stage learning
curriculum. It is a Python console app for managing sample ("시료") orders and
production, used by an order manager and a production manager. Customers
request samples by email; the order manager records orders; the production
manager registers samples and approves/rejects orders.

The full domain spec lives at `../description.md` (workspace root, one level
up from this repo) — that file is the authoritative source for menus, fields,
and business rules. Re-read it directly rather than trusting a summary if
anything here seems stale.

## Curriculum and where this repo fits

The `S-Semi` workspace contains 5 separate git repos, each with its own GitHub
origin under user `yulgon`, built in this order:

1. **ConsoleMVC** (`ConsoleMVC-yulgon-09013121`) — PoC. Model/View/Controller
   package structure and separation of concerns for the console UI. This
   becomes the actual UI code `SampleOrderSystem` uses.
2. **DataPersistence** (`DataPersistence-yulgon-09013121`) — PoC. JSON-based
   data save/load with full CRUD.
3. **DataMonitor** (`DataMonitor-yulgon-09013121`) — PoC. Admin tool for
   real-time console inspection of stored data state.
4. **DummyDataGenerator** (`DummyDataGenerator-yulgon-09013121`) — PoC.
   Generates dummy test data, written into the connected JSON DB.
5. **SampleOrderSystem** (this repo) — the real, integrated program. Not a
   PoC: it combines the pieces proven out in stages 1-4 into a working
   system, and is where `claude.md` (this file), `PRD.md`, and `PLAN.md` are
   meant to live per the workspace's own process description.

### Status

| Stage | Status |
|---|---|
| 1. ConsoleMVC | **Done** (2026-07-15). Menu/screen-flow PoC — Model/View/Controller package structure with no real business logic yet (every action echoes input or shows a placeholder). 9 tasks, 28 passing tests, final whole-branch review "Ready to merge: Yes". 10 commits on `main`, kept local. |
| 2. DataPersistence | **Done** (2026-07-15). Generic `JsonRepository` — one JSON file per collection, dict in/dict out, sequential auto-increment ids via max+1, deliberately no domain-specific types. 5 tasks, 12 passing tests, "Ready to merge: Yes". 7 commits on `main`, kept local. |
| 3. DataMonitor | **Done** (2026-07-15). Read-only admin console — `reader.py` (list/read collections, own minimal impl) + `MonitorConsole` (list → detail → refresh/back/exit). 5 tasks, 17 passing tests. Final whole-branch review caught a real cross-task crash (a `*.json`-named directory or malformed JSON file crashed the app when selected/refreshed) — fixed and re-verified. 9 commits on `main`, kept local. |
| 4. DummyDataGenerator | **Done** (2026-07-15). Interactive menu tool generating dummy Sample/Order records — `JsonStore` (own max+1 id reimplementation), `factory.py` (structural-only tests for randomness), `GeneratorConsole` (blocks order generation until samples exist, references random existing sample_id). 5 tasks, 16 passing tests, "Ready to merge: Yes" — no cross-task bugs this time. 7 commits on `main`, kept local. |
| 5. SampleOrderSystem | **Next up** (this repo currently only has this `CLAUDE.md` committed). |

All 4 PoC stages built via `superpowers:subagent-driven-development` (fresh
implementer subagent per task, task-scoped review, final whole-branch
review) — see each stage's own repo for its design spec and plan under
`docs/superpowers/`.

`PRD.md` and `PLAN.md` for this repo have not been written yet — now that
all 4 PoC stages are done, the next step is brainstorming this repo's real
integration: reusing ConsoleMVC's MVC split, DataPersistence's
`JsonRepository`, DataMonitor's read/refresh pattern, and
DummyDataGenerator's factories, wired to real Sample/Order business logic
(status transitions, stock math, production scheduling) that none of the
4 PoCs implemented.

## Domain summary

**Roles:**
- 고객 (customer) — requests samples by email (outside the system)
- 주문 담당자 (order manager) — writes orders based on customer requests
- 생산 담당자 (production manager) — registers samples, approves/rejects orders

**Order statuses:** `RESERVED` → (`REJECTED` | `CONFIRMED` | `PRODUCING` →
`CONFIRMED`) → `RELEASE`

**Key entities:**
- `Sample`: sample_id, name, avg_production_time, yield_rate, stock
- `Order`: order_id, sample_id, customer, qty, status

**Main menu (status bar + 7 options):**
0. Status bar — 등록시료, 총 재고, 전체주문, 대기중인 생산라인
1. 시료 관리 — 등록 / 조회 / 검색
2. 시료 주문 — 고객 주문 접수 (→ RESERVED)
3. 주문 (승인/거절) — 목록 확인, 승인 (재고 충분 → CONFIRMED, 부족 → PRODUCING), 거절 (→ REJECTED)
4. 모니터링 — 상태별 주문량, 시료별 재고량(여유/부족/고갈)
5. 출고 처리 — CONFIRMED → RELEASE
6. 생산 라인 — FIFO 큐, 실 생산량 = 부족분/수율, 총 생산시간 = 평균생산시간 × 실생산량, 완료 시 PRODUCING → CONFIRMED
7. 종료

## Conventions established so far (apply across all 5 repos)

- **Language/stack:** Python 3, pytest for tests.
- **Commit messages:** English, even though menu labels/domain terms stay in
  Korean (matching `description.md`).
- **Step-by-step commits:** every module is implemented in small increments,
  each ending in its own git commit — not one big commit at the end. This was
  an explicit user requirement, not just a style preference.
- **Process per module:** brainstorming → design spec
  (`docs/superpowers/specs/`) → implementation plan
  (`docs/superpowers/plans/`) → execution via
  `superpowers:subagent-driven-development` (fresh implementer subagent per
  task, task-scoped review, final whole-branch review).
- **Branch strategy:** work happens directly on `main` in each repo (no
  feature branches, no PRs) — this is a solo learning project, confirmed
  explicitly with the user for ConsoleMVC and expected to hold for the
  remaining stages unless stated otherwise.
- **PoC scope discipline:** each PoC stage implements only what its own
  concern requires (e.g., ConsoleMVC = menu/screen flow only, no persistence,
  no computed business logic) and defers the next concern to its own stage.

## Known repo-wide risk (not yet resolved)

`.mcp.json` at the workspace root (`C:\reviewer\work\S-Semi\.mcp.json`)
contains a plaintext GitHub PAT. If that folder is ever shared or committed,
the token would leak. Not yet addressed — rotate/gitignore before sharing the
workspace.
