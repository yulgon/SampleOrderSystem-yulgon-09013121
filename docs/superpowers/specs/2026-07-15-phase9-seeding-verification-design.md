# Phase 9 — Seeding & Manual End-to-End Verification — Design

## Context

This is Phase 9, the final phase of the 9-phase `SampleOrderSystem`
roadmap (see `PLAN.md`). Phases 1-8 built the complete system: model,
persistence, every PRD §6 menu, and a real `AppController`. This phase
seeds realistic data (reusing `DummyDataGenerator`'s *pattern* — a
standalone script generating data via the real repositories — not the
separate PoC repo itself, since ids must match this repo's own scheme,
which they already do by construction) and manually walks the full system
end-to-end against it.

## Scope

**In scope:** `scripts/seed_data.py` — a standalone script (not a PRD
menu item) that populates the real `data/` directory with a small, fixed
(non-random) dataset: 4 samples spanning every stock-health case (여유/
부족 예정/고갈/중간) and 5 orders (all `RESERVED`) referencing them,
chosen so that approving each order exercises both the sufficient-stock
and insufficient-stock paths. A manual verification checklist (recorded
in the implementation plan and executed against the running app).

**Out of scope:** any new application code — Phases 1-8 already implement
every behavior being verified here. This script only calls existing
`SampleRepository`/`OrderRepository` methods.

## Fixed Seed Dataset

**Samples:**
| # | name | avg_production_time | yield_rate | stock | intent |
|---|---|---|---|---|---|
| 1 | Sample A | 2.0 | 0.9 | 20 | 여유 — its order fits within stock |
| 2 | Sample B | 1.5 | 0.8 | 2 | 부족 예정 — its order exceeds stock by 8 |
| 3 | Sample C | 3.0 | 0.95 | 0 | 고갈 — its order is entirely a shortfall |
| 4 | Sample D | 2.5 | 0.85 | 10 | 중간 — two orders, both fit |

**Orders (all `RESERVED`):**
| sample | qty | expected on approval |
|---|---|---|
| Sample A | 5 | sufficient stock (20≥5) → `CONFIRMED` |
| Sample B | 10 | insufficient (2<10) → `PRODUCING`, shortfall=8 |
| Sample C | 3 | insufficient (0<3) → `PRODUCING`, shortfall=3 |
| Sample D | 5 | sufficient (10≥5) → `CONFIRMED`, stock 10→5 |
| Sample D | 3 | sufficient (5≥3 once the first D order above is approved first) → `CONFIRMED`, stock 5→2 |

## Script Behavior

```
scripts/seed_data.py:
  if data/ already exists: print a message and exit without writing
                            (never silently overwrite existing state)
  else: create the 4 samples and 5 orders above via
        SampleRepository/OrderRepository (real base_dir="data")
        print each created sample/order's assigned id and a summary
        re-read everything back via the same repositories and assert
        the counts/values match what was just written (self-check;
        exits with a clear error if not, rather than silently
        continuing on a filesystem problem)
```

## Manual Verification Checklist

Executed against the real running app (`python main.py`) after seeding,
recorded as a checklist in the implementation plan:

1. 시료 관리: 조회 shows all 4 samples with correct stock; 검색 finds a
   sample by partial name.
2. 모니터링 (initial): 주문량 확인 shows `RESERVED: 5`, others 0;
   재고량 확인 shows one line per sample — A=여유, B=부족, C=고갈, D=여유.
3. 주문 (승인/거절): approve the Sample A order → `CONFIRMED`, stock
   20→15 (note: A's stock isn't touched by seeding math above since A's
   order qty=5 ≤ 20, so approval deducts 5 → 15). Approve the Sample B
   order → `PRODUCING`, a queue entry appears. Approve the Sample C
   order → `PRODUCING`, another queue entry. Approve both Sample D
   orders in order → both `CONFIRMED`, stock 10→5→2.
4. 생산 라인: 생산 현황 shows the head entry (Sample B's, queued first);
   대기 주문 확인 shows both queued entries with correct cumulative
   예상완료; 생산 완료 처리 twice (B then C) — stock restored by each
   shortfall, both orders become `CONFIRMED`, queue ends empty.
5. 출고 처리: release every `CONFIRMED` order (A, both D orders, B, C) →
   all `RELEASE`.
6. 모니터링 (final): 주문량 확인 shows `RELEASE: 5`, others 0; 재고량
   확인 reflects final stock levels with zero outstanding demand (all
   여유, since no orders remain `RESERVED`/`PRODUCING`).
7. Restart `python main.py` (fresh process) and confirm the status bar
   and `시료 관리`/`모니터링` immediately reflect the persisted final
   state — proving the data survives a process restart, not just an
   in-memory session.

## Error Handling

The script refuses to run if `data/` already exists (protects against
silently clobbering the user's own manual testing state) — this is the
only "error path" in scope; the seeded data itself has no invalid values
to guard against since it's fixed and pre-validated against
`Sample`/`Order`'s own `__post_init__` rules by inspection.

## Testing

No pytest suite for this script (it's a one-time developer tool, not
application code covered by the project's TDD convention). Its own
built-in self-check (re-read and assert) is the verification mechanism,
plus the manual checklist above executed against the real app.

## Process Note

Same convention as prior phases for commit staging where applicable
(`[GREEN]`-only for this script since there's no pytest RED/GREEN cycle
for it — see plan for exact commit breakdown), developed on branch
`phase-9-seeding-verification`, merged via a PR the user reviews and
merges manually. This is the final phase of the S-Semi curriculum.
