# Phase 9 (Seeding & Manual End-to-End Verification) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan has no automated pytest suite for Task 1 (it's a standalone developer script, not application code) — its steps use direct execution + a built-in self-check instead of a RED/GREEN pytest cycle. Task 2 is a manual verification exercise recorded as a checklist, not code.

**Goal:** Seed the real `data/` directory with a small, fixed dataset covering every stock-health case, then manually walk the complete running application end-to-end against it — the final acceptance check for the entire 9-phase `SampleOrderSystem` project.

**Architecture:** `scripts/seed_data.py` is a standalone script (outside the `model`/`view`/`controller`/`persistence` application packages) that calls `SampleRepository`/`OrderRepository` directly with a fixed dataset, then re-reads and asserts against what it wrote as a self-check.

**Tech Stack:** Python 3, stdlib only (`os`, `sys`).

## Global Constraints

- The script refuses to run if `data/` already exists (never silently overwrites) — prints a message and exits instead.
- All 5 orders are created as `RESERVED`; no other status is seeded directly, since real status transitions must go through the app's actual business logic during manual verification (register→reserve is the natural starting point, not a shortcut around approval/production/release).
- The dataset itself is fixed (not random) — see the design spec's tables for exact values.
- Commit staging: `[GREEN]`-only for Task 1 (no pytest RED/GREEN cycle for a standalone script — same convention as this project's integration-only commits); Task 2 has no code commit, just a verification log.
- Developed on branch `phase-9-seeding-verification` — no direct commits to `main`.

---

### Task 1: `scripts/seed_data.py`

**Files:**
- Create: `scripts/seed_data.py`

**Interfaces:**
- Consumes: `Sample` from `model/sample.py`; `Order`, `OrderStatus` from `model/order.py`; `SampleRepository`, `OrderRepository`
- Produces: a runnable script (`python scripts/seed_data.py`, run from the repo root) with no importable symbols needed elsewhere

- [ ] **Step 1: Write the script**

Create `scripts/seed_data.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.sample import Sample
from model.order import Order, OrderStatus
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository


SAMPLES = [
    {"name": "Sample A", "avg_production_time": 2.0, "yield_rate": 0.9, "stock": 20},
    {"name": "Sample B", "avg_production_time": 1.5, "yield_rate": 0.8, "stock": 2},
    {"name": "Sample C", "avg_production_time": 3.0, "yield_rate": 0.95, "stock": 0},
    {"name": "Sample D", "avg_production_time": 2.5, "yield_rate": 0.85, "stock": 10},
]

# (index into SAMPLES, order qty)
ORDERS = [
    (0, 5),   # Sample A: sufficient (20 >= 5)
    (1, 10),  # Sample B: insufficient (2 < 10), shortfall 8
    (2, 3),   # Sample C: insufficient (0 < 3), shortfall 3
    (3, 5),   # Sample D: sufficient (10 >= 5)
    (3, 3),   # Sample D: sufficient (5 >= 3, after the order above is approved)
]


def main():
    if os.path.isdir("data"):
        print("data/ 디렉토리가 이미 존재합니다. 기존 데이터를 보호하기 위해 시딩을 중단합니다.")
        print("새로 시딩하려면 기존 data/ 디렉토리를 직접 삭제한 뒤 다시 실행하세요.")
        return

    sample_repo = SampleRepository()
    order_repo = OrderRepository()

    created_samples = []
    for spec in SAMPLES:
        sample = sample_repo.create(Sample(**spec))
        created_samples.append(sample)
        print(f"시료 생성: ID={sample.sample_id}, 이름={sample.name}, 재고={sample.stock}")

    created_orders = []
    for sample_index, qty in ORDERS:
        sample = created_samples[sample_index]
        order = order_repo.create(
            Order(sample_id=sample.sample_id, customer="Acme", qty=qty, status=OrderStatus.RESERVED)
        )
        created_orders.append(order)
        print(
            f"주문 생성: ID={order.order_id}, 시료ID={order.sample_id}, "
            f"수량={order.qty}, 상태={order.status}"
        )

    reread_samples = sample_repo.list_all()
    reread_orders = order_repo.list_all()

    assert len(reread_samples) == len(SAMPLES), (
        f"시료 개수 불일치: 기대 {len(SAMPLES)}, 실제 {len(reread_samples)}"
    )
    assert len(reread_orders) == len(ORDERS), (
        f"주문 개수 불일치: 기대 {len(ORDERS)}, 실제 {len(reread_orders)}"
    )
    for expected, actual in zip(created_samples, reread_samples):
        assert expected == actual, f"시료 데이터 불일치: {expected} != {actual}"
    for expected, actual in zip(created_orders, reread_orders):
        assert expected == actual, f"주문 데이터 불일치: {expected} != {actual}"

    print(f"\n시딩 완료: 시료 {len(reread_samples)}개, 주문 {len(reread_orders)}건 (재확인 통과)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script from the repo root and confirm it seeds correctly**

Run: `python scripts/seed_data.py`
Expected: prints 4 "시료 생성" lines, 5 "주문 생성" lines, and ends with
"시딩 완료: 시료 4개, 주문 5건 (재확인 통과)" — no assertion errors, no
tracebacks. Confirm `data/samples.json` has 4 records and
`data/orders.json` has 5 records, all `status: "RESERVED"`.

- [ ] **Step 3: Run it again to confirm the already-exists guard works**

Run: `python scripts/seed_data.py` (a second time, without deleting `data/`)
Expected: prints the "data/ 디렉토리가 이미 존재합니다..." message and exits
without modifying anything — confirm `data/samples.json`/`data/orders.json`
are unchanged (still 4 samples / 5 orders) after this second run.

- [ ] **Step 4: Commit**

```bash
git add scripts/seed_data.py
git commit -m "[GREEN] add scripts/seed_data.py for manual verification seeding"
```

---

### Task 2: Manual end-to-end verification

**Files:**
- Create: `docs/superpowers/PHASE9-VERIFICATION.md` (the executed checklist with actual results recorded)

**No automated tests** — this task IS the manual verification exercise
for the entire project. Do not delete `data/` before starting (it should
still hold Task 1's seeded state, confirmed unchanged by Task 1's Step 3).

- [ ] **Step 1: Walk the full checklist against the real running app**

Run `python main.py` and, using the seeded data from Task 1, execute each
item below in order (approving/producing/releasing in the sequence shown
so stock numbers land as predicted):

1. **시료 관리** — 조회 shows all 4 samples with stock 20/2/0/10; 검색
   for "Sample" finds all 4, search for "B" finds only Sample B.
2. **모니터링 (initial)** — 주문량 확인 shows `RESERVED: 5`, `CONFIRMED: 0`,
   `PRODUCING: 0`, `RELEASE: 0`. 재고량 확인 shows Sample A=여유, B=부족,
   C=고갈, D=여유.
3. **주문 (승인/거절)** — approve, in this order: Sample A's order (→
   `CONFIRMED`, stock 20→15), Sample D's qty=5 order (→ `CONFIRMED`,
   stock 10→5), Sample D's qty=3 order (→ `CONFIRMED`, stock 5→2),
   Sample B's order (→ `PRODUCING`, queue entry created, shortfall=8,
   actual_qty=`ceil(8/0.8)`=10, total_time=1.5×10=15.0), Sample C's order
   (→ `PRODUCING`, queue entry created, shortfall=3, actual_qty=
   `ceil(3/0.95)`=4, total_time=3.0×4=12.0).
4. **생산 라인** — 생산 현황 shows Sample B's entry (queued first,
   예상완료=15.0). 대기 주문 확인 shows both entries, cumulative
   예상완료 15.0 then 27.0 (15.0+12.0). 생산 완료 처리 (completes
   Sample B's entry: stock 2→10, order `CONFIRMED`), 생산 완료 처리
   again (completes Sample C's entry: stock 0→3, order `CONFIRMED`),
   대기 주문 확인 now shows "대기 중인 생산이 없습니다."
5. **출고 처리** — release all 5 orders (now all `CONFIRMED`) one at a
   time; each becomes `RELEASE`.
6. **모니터링 (final)** — 주문량 확인 shows `RELEASE: 5`, others 0.
   재고량 확인 shows all 4 samples as 여유 (no outstanding
   `RESERVED`/`PRODUCING` demand remains anywhere).
7. **Restart** — exit (menu 7), then run `python main.py` again (a fresh
   process) and confirm the status bar immediately shows 등록시료=4,
   총재고=(15+10+3+2=30), 전체주문=5, 대기중인생산라인=0 — proving the
   final state persisted correctly to disk rather than only existing
   in-memory.

- [ ] **Step 2: Record the results**

Create `docs/superpowers/PHASE9-VERIFICATION.md` with the checklist above
and, for each item, what was actually observed (should match the expected
values exactly; note and investigate any discrepancy before proceeding —
a discrepancy here means a real bug in Phases 1-8, not something to
explain away).

- [ ] **Step 3: Clean up and commit**

```bash
rm -rf data
git add docs/superpowers/PHASE9-VERIFICATION.md
git commit -m "Record Phase 9 manual end-to-end verification results"
```

## Self-Review Notes

- **Spec coverage:** every menu (시료 관리, 시료 주문 — implicitly exercised
  since the seed script performs the equivalent of reservation directly,
  주문 승인/거절, 생산 라인, 출고 처리, 모니터링) is walked at least once
  with predictable, pre-computed expected values.
- **Placeholder scan:** no TBD/TODO; the script is complete and the
  checklist has concrete expected values, not vague descriptions.
- **Type consistency:** `Sample`/`Order` construction in the script uses
  the exact same field names as `model/sample.py`/`model/order.py`;
  `SampleRepository()`/`OrderRepository()`'s default `base_dir="data"`
  matches every other component's default, so the script and the app
  operate on the same directory without needing to pass `base_dir`
  explicitly anywhere.
