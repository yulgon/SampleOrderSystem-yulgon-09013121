# Phase 1 — Model + Persistence — Design

## Context

This is Phase 1 of the 9-phase `SampleOrderSystem` roadmap (see `PLAN.md`),
the final, real (non-PoC) stage of the S-Semi curriculum. It builds the
foundation everything else depends on: real `Sample`/`Order` dataclasses
and a working JSON persistence layer with system-assigned sequential ids
(per `PRD.md` §5.1/§5.2 and the decisions log's #4). No console UI exists
yet — that starts in Phase 2.

Unlike the 4 PoC stages (separate git repos, no code sharing), this repo
can reuse its own code freely across phases. The generic `JsonRepository`
here is a fresh implementation informed by `DataPersistence`'s proven
design (same max+1 id scheme, same CRUD shape), not an import from that
separate repo.

## Scope

**In scope:** `Sample`/`Order` dataclasses with `to_dict()`/`from_dict()`
and minimal `__post_init__` validation; a generic `JsonRepository`
(create/get/list_all/update/delete, max+1 sequential ids); typed
`SampleRepository`/`OrderRepository` wrappers that convert between
dataclasses and the generic repository's dicts.

**Out of scope:** console UI/menus (Phase 2+), business logic — stock
deduction, status transitions beyond simple field storage, production
scheduling (Phases 4-6). This phase only proves the data foundation works.

## Package Structure

```
SampleOrderSystem-yulgon-09013121/
  model/
    __init__.py
    sample.py    # Sample dataclass
    order.py     # Order dataclass + OrderStatus
  persistence/
    __init__.py
    repository.py         # JsonRepository — generic, dict-based
    sample_repository.py  # SampleRepository — Sample <-> dict via JsonRepository("samples")
    order_repository.py   # OrderRepository — Order <-> dict via JsonRepository("orders")
```

## Fields and Validation

- **Sample:** `sample_id` (system-assigned), `name`, `avg_production_time`,
  `yield_rate`, `stock`. `__post_init__` validates: `avg_production_time >
  0`, `0 <= yield_rate <= 1`, `stock >= 0` — raises `ValueError` on
  violation.
- **Order:** `order_id` (system-assigned), `sample_id`, `customer`, `qty`,
  `status`. `__post_init__` validates: `qty > 0`, `status` is one of
  `OrderStatus`'s 5 values — raises `ValueError` on violation.
- Both dataclasses implement `to_dict()` (plain dict, `id` field included
  when present) and `from_dict(data)` (classmethod, reconstructs the
  dataclass — including the id — from a stored dict).

## Data Flow

`SampleRepository.create(sample)`: calls `sample.to_dict()`, strips any
`id`/`sample_id` key from what's passed to `JsonRepository.create()` (which
assigns the real id), then wraps the returned dict (now including the
assigned id) back into a `Sample` via `from_dict()` and returns it.
`get`/`list_all`/`update`/`delete` follow the same wrap/unwrap pattern —
the repository wrapper is the only place that knows about the
dataclass/dict boundary; `JsonRepository` itself stays fully generic.

## Error Handling

`JsonRepository` behaves exactly like `DataPersistence`'s version: a
missing file is an empty collection (no exception); `get`/`update`/`delete`
against a missing id return `None`/`None`/`False`. Dataclass validation
errors (`ValueError` from `__post_init__`) propagate as-is — this phase
doesn't catch or wrap them; a later phase's controller layer is what turns
these into user-facing console messages.

## Testing

`JsonRepository` is tested against real file I/O via pytest's `tmp_path`
fixture, covering the same CRUD cases proven out in `DataPersistence`.
`Sample`/`Order` get unit tests for `to_dict()`/`from_dict()` round-tripping
and for both the valid and invalid (`ValueError`-raising) sides of
`__post_init__` validation. `SampleRepository`/`OrderRepository` get
integration tests (real `tmp_path`) proving create/get/list_all/
update/delete round-trip correctly as dataclasses, not just as dicts.

## Process Note

This phase (and every phase from here on) follows RED/GREEN/REVIEW commit
staging (see `CLAUDE.md`) and is developed on its own feature branch
(`phase-1-model-persistence`), merged via a PR the user reviews and merges
manually — no direct commits to `main`.
