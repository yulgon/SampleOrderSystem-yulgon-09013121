from model.production_queue_entry import ProductionQueueEntry
from persistence.production_queue_repository import ProductionQueueRepository


def _make_entry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0):
    return ProductionQueueEntry(
        order_id=order_id, sample_id=sample_id, shortfall=shortfall,
        actual_qty=actual_qty, total_time=total_time,
    )


def test_create_returns_entry_with_assigned_id(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    created = repo.create(_make_entry())
    assert isinstance(created, ProductionQueueEntry)
    assert created.entry_id == 1
    assert created.order_id == 1


def test_list_all_returns_all_entries_in_order(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry(order_id=1))
    repo.create(_make_entry(order_id=2))
    assert [e.order_id for e in repo.list_all()] == [1, 2]


def test_create_ignores_preset_id_and_assigns_a_fresh_one(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry(order_id=1))
    second = ProductionQueueEntry(
        order_id=2, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0, entry_id=1,
    )
    created = repo.create(second)
    assert created.entry_id == 2
    assert len(repo.list_all()) == 2


def test_delete_removes_entry_and_returns_true(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    entry = repo.create(_make_entry())
    assert repo.delete(entry.entry_id) is True
    assert repo.list_all() == []


def test_delete_returns_false_for_missing_id(tmp_path):
    repo = ProductionQueueRepository(base_dir=str(tmp_path))
    repo.create(_make_entry())
    assert repo.delete(999) is False
    assert len(repo.list_all()) == 1
