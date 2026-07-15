# Phase 9 — Manual End-to-End Verification

This is the final acceptance check for the entire 9-phase SampleOrderSystem
project. It walks the complete running application (`python main.py`)
through every menu, using the data seeded by Task 1 (4 samples, 5
`RESERVED` orders), and confirms every pre-computed expected value is met
exactly.

**Method:** the full menu-driven session was executed as a single scripted
stdin sequence (traced against `controller/app_controller.py` and all 6
sub-controllers so every prompt is answered correctly and in the exact
approve/produce/release order the checklist requires), then run twice for
independent confirmation (once with default console encoding, once with
`PYTHONIOENCODING=utf-8` for clean transcript capture). Both runs produced
byte-identical final `data/*.json` state. The final run's process output is
the transcript referenced below.

Command used:

```
python main.py < stdin_sequence.txt
```

with a fresh copy of Task 1's seeded `data/samples.json` /
`data/orders.json` / `data/production_queue.json` (`[]`) in place before
each run.

## Checklist results

### 1. 시료 관리

| Check | Expected | Actual | Match |
|---|---|---|---|
| 조회 (list all) | stock 20/2/0/10 for A/B/C/D | `ID=1 Sample A 재고=20`, `ID=2 Sample B 재고=2`, `ID=3 Sample C 재고=0`, `ID=4 Sample D 재고=10` | ✅ |
| 검색 "Sample" | finds all 4 | all 4 samples returned | ✅ |
| 검색 "B" | finds only Sample B | only `ID=2, 이름=Sample B, 재고=2` returned | ✅ |

### 2. 모니터링 (initial)

| Check | Expected | Actual | Match |
|---|---|---|---|
| 주문량 확인 | RESERVED:5, CONFIRMED:0, PRODUCING:0, RELEASE:0 | `RESERVED: 5건`, `CONFIRMED: 0건`, `PRODUCING: 0건`, `RELEASE: 0건` | ✅ |
| 재고량 확인 | A=여유, B=부족, C=고갈, D=여유 | `Sample A 상태=여유`, `Sample B 상태=부족`, `Sample C 상태=고갈`, `Sample D 상태=여유` | ✅ |

### 3. 주문 (승인/거절)

Approved in the required order: Sample A's order (id 1), Sample D's qty=5
order (id 4), Sample D's qty=3 order (id 5), Sample B's order (id 2),
Sample C's order (id 3).

| Order | Expected | Actual | Match |
|---|---|---|---|
| A (id 1, qty 5) | → CONFIRMED, stock 20→15 | `승인 완료 (재고 차감): ID=1, 상태=CONFIRMED`; running total stock confirms 20→15 | ✅ |
| D (id 4, qty 5) | → CONFIRMED, stock 10→5 | `승인 완료 (재고 차감): ID=4, 상태=CONFIRMED`; running total confirms 10→5 | ✅ |
| D (id 5, qty 3) | → CONFIRMED, stock 5→2 | `승인 완료 (재고 차감): ID=5, 상태=CONFIRMED`; running total confirms 5→2 | ✅ |
| B (id 2, qty 10) | → PRODUCING, queue entry, shortfall=8, actual_qty=ceil(8/0.8)=10, total_time=1.5×10=15.0 | `재고 부족 - 생산 등록: 주문ID=2, 부족분=8, 실생산량=10, 총생산시간=15.0` | ✅ |
| C (id 3, qty 3) | → PRODUCING, queue entry, shortfall=3, actual_qty=ceil(3/0.95)=4, total_time=3.0×4=12.0 | `재고 부족 - 생산 등록: 주문ID=3, 부족분=3, 실생산량=4, 총생산시간=12.0` | ✅ |

Status bar after all 5 approvals: `등록시료: 4 | 총 재고: 19 | 전체주문: 5 |
대기중인 생산라인: 2` — total stock 15(A)+2(B, unchanged, PRODUCING)+0(C,
unchanged, PRODUCING)+2(D) = 19, matches arithmetic. ✅

### 4. 생산 라인

| Check | Expected | Actual | Match |
|---|---|---|---|
| 생산 현황 | Sample B's entry queued first, 예상완료=15.0 | `순서=1, 주문번호=2, 시료=Sample B, ..., 예상완료=15.0` | ✅ |
| 대기 주문 확인 | both entries, cumulative 15.0 then 27.0 | `순서=1 ... 예상완료=15.0` then `순서=2, 주문번호=3, 시료=Sample C, ..., 예상완료=27.0` (15.0+12.0) | ✅ |
| 생산 완료 처리 (1st) | completes Sample B's entry: stock 2→10, order→CONFIRMED | `생산 완료 처리: 주문ID=2, 재고 +8, 상태=CONFIRMED` (stock 2+8=10) | ✅ |
| 생산 완료 처리 (2nd) | completes Sample C's entry: stock 0→3, order→CONFIRMED | `생산 완료 처리: 주문ID=3, 재고 +3, 상태=CONFIRMED` (stock 0+3=3) | ✅ |
| 대기 주문 확인 (after) | "대기 중인 생산이 없습니다." | `대기 중인 생산이 없습니다.` | ✅ |

Status bar after production complete: `등록시료: 4 | 총 재고: 30 |
전체주문: 5 | 대기중인 생산라인: 0` (15+10+3+2=30). ✅

### 5. 출고 처리

All 5 orders (all now CONFIRMED) released one at a time.

| Order id | Expected | Actual | Match |
|---|---|---|---|
| 1 | → RELEASE | `출고 완료: 주문ID=1, 상태=RELEASE` | ✅ |
| 2 | → RELEASE | `출고 완료: 주문ID=2, 상태=RELEASE` | ✅ |
| 3 | → RELEASE | `출고 완료: 주문ID=3, 상태=RELEASE` | ✅ |
| 4 | → RELEASE | `출고 완료: 주문ID=4, 상태=RELEASE` | ✅ |
| 5 | → RELEASE | `출고 완료: 주문ID=5, 상태=RELEASE` | ✅ |

### 6. 모니터링 (final)

| Check | Expected | Actual | Match |
|---|---|---|---|
| 주문량 확인 | RELEASE:5, others 0 | `RESERVED: 0건`, `CONFIRMED: 0건`, `PRODUCING: 0건`, `RELEASE: 5건` | ✅ |
| 재고량 확인 | all 4 samples 여유 | `Sample A 재고=15 상태=여유`, `Sample B 재고=10 상태=여유`, `Sample C 재고=3 상태=여유`, `Sample D 재고=2 상태=여유` | ✅ |

### 7. Restart (persistence check)

Exited via menu option 7 (`프로그램을 종료합니다.`), then launched
`python main.py` again as a **fresh process** (no shared in-memory state)
and observed the very first line printed:

```
[상태] 등록시료: 4 | 총 재고: 30 | 전체주문: 5 | 대기중인 생산라인: 0
```

| Field | Expected | Actual | Match |
|---|---|---|---|
| 등록시료 | 4 | 4 | ✅ |
| 총재고 | 15+10+3+2=30 | 30 | ✅ |
| 전체주문 | 5 | 5 | ✅ |
| 대기중인 생산라인 | 0 | 0 | ✅ |

Confirms the final state was persisted to `data/*.json` on disk, not just
held in memory — a brand-new process correctly reconstructs it.

## Result

**Every checklist item matched its predicted value exactly. No
discrepancies were found.** The system correctly composes all 9 phases:
sample registration/search, order intake, approve/reject with stock-vs-
shortfall branching, FIFO production queue with correct shortfall/actual_qty/
total_time math, production completion restoring stock and confirming
orders, release processing, monitoring aggregation (order-volume counts and
stock-level classification), the top-level status bar, and JSON persistence
across process restarts.

## Cleanup

After verification, `data/` was removed (`rm -rf data`) so no seeded state
lingers in the repository's working tree; the running application recreates
it fresh from an empty state on next use.

## Supplementary Verification: Interactive Order Intake + Reject Path

The whole-branch review of Phase 9 flagged a gap in the walkthrough above:
`scripts/seed_data.py` creates all 5 orders directly via
`OrderRepository.create()`, bypassing the console's own 시료 주문 (order
reservation) menu entirely, and the approve/reject checklist above only ever
exercised approvals — 주문 거절 (reject) was never driven through the live
console by a human, even though both paths are covered by
`tests/test_order_controller.py`. This supplementary check closes that gap by
exercising the live 시료 주문 menu and the 거절 path interactively, against a
brand-new empty `data/` directory (no seeded state at all), tracing the exact
prompt sequence against `controller/app_controller.py`,
`controller/sample_controller.py`, and `controller/order_controller.py`
(`run_reserve` and the `3. 주문 거절` branch of `run_approve_reject`) before
scripting stdin.

**Method:** `python main.py` run once with `PYTHONIOENCODING=utf-8` against a
directory with no pre-existing `data/`, driven by a single scripted stdin
sequence (`stdin_supplementary.txt`, deleted after the run):

```
1
1
Sample X
2.0
0.9
5
4
2
1
Customer A
3
3
3
1
4
4
1
3
7
```

This drives: 시료 관리 → 시료 등록 (register "Sample X"), back to main menu,
시료 주문 (reserve an order against sample ID 1 for "Customer A", qty 3), back
to main menu, 주문 (승인/거절) → 주문 거절 (reject order ID 1), back to main
menu, 모니터링 → 주문량 확인, then 종료.

Command used:

```
PYTHONIOENCODING=utf-8 python main.py < stdin_supplementary.txt
```

### Results

| Step | Expected | Actual | Match |
|---|---|---|---|
| a. 시료 등록 | new sample created, ID=1, echoed back with all fields | `시료 등록 완료: ID=1, 이름=Sample X, 평균생산시간=2.0, 수율=0.9, 재고=5` | ✅ |
| b. 시료 주문 (menu 2) reserve | order created via the live 시료 ID / 고객명 / 주문 수량 prompts, echoed back with assigned order_id and status RESERVED | `주문 접수 완료: ID=1, 시료ID=1, 고객명=Customer A, 수량=3, 상태=RESERVED` | ✅ |
| c. 주문 (승인/거절) → 주문 거절 | order ID=1 transitions RESERVED → REJECTED | `주문 거절 완료: ID=1, 상태=REJECTED` | ✅ |
| d. 모니터링 → 주문량 확인 | RESERVED/CONFIRMED/PRODUCING/RELEASE all 0 (the only order is REJECTED, excluded from all 4 counted statuses) | `RESERVED: 0건`, `CONFIRMED: 0건`, `PRODUCING: 0건`, `RELEASE: 0건` | ✅ |

Status bar after the reject: `[상태] 등록시료: 1 \| 총 재고: 5 \| 전체주문: 0
\| 대기중인 생산라인: 0` — `전체주문` correctly drops to 0 since
`AppController._show_status_bar` counts only non-`REJECTED` orders, and the
one order that existed is now `REJECTED`; sample stock stays at 5 (reject
never touches stock, since the order never reached `CONFIRMED`). Confirmed
against the final `data/orders.json`:

```json
[
  {
    "id": 1,
    "sample_id": 1,
    "customer": "Customer A",
    "qty": 3,
    "status": "REJECTED"
  }
]
```

**No tracebacks or unexpected output occurred at any point in the run.**

### Result

Both flows the original walkthrough skipped — the live 시료 주문 intake menu
and the 주문 거절 path — were exercised through the actual running console
and matched every predicted value exactly. Combined with the original
checklist above (which covered registration, search, approval variants,
production queue, release, monitoring, and persistence), the full set of
Phase 9 order-lifecycle transitions (`RESERVED` → `REJECTED`, `RESERVED` →
`CONFIRMED`, `RESERVED` → `PRODUCING` → `CONFIRMED` → `RELEASE`) has now been
driven manually through the live console at least once each.

`data/` and `stdin_supplementary.txt` were removed after this check so no
state lingers in the working tree.
