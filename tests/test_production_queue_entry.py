import pytest

from model.production_queue_entry import ProductionQueueEntry


def test_to_dict_includes_id_when_present():
    entry = ProductionQueueEntry(
        order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0, entry_id=1
    )
    assert entry.to_dict() == {
        "id": 1,
        "order_id": 1,
        "sample_id": 1,
        "shortfall": 8,
        "actual_qty": 16,
        "total_time": 32.0,
    }


def test_to_dict_omits_id_when_none():
    entry = ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=32.0)
    assert "id" not in entry.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "order_id": 1, "sample_id": 1, "shortfall": 8, "actual_qty": 16, "total_time": 32.0}
    entry = ProductionQueueEntry.from_dict(data)
    assert entry.entry_id == 1
    assert entry.to_dict() == data


def test_raises_on_non_positive_shortfall():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=0, actual_qty=16, total_time=32.0)


def test_raises_on_non_positive_actual_qty():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=0, total_time=32.0)


def test_raises_on_non_positive_total_time():
    with pytest.raises(ValueError):
        ProductionQueueEntry(order_id=1, sample_id=1, shortfall=8, actual_qty=16, total_time=0)
