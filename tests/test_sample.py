import pytest

from model.sample import Sample


def test_to_dict_includes_id_when_present():
    sample = Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10, sample_id=1)
    assert sample.to_dict() == {
        "id": 1,
        "name": "Sample A",
        "avg_production_time": 2.5,
        "yield_rate": 0.9,
        "stock": 10,
    }


def test_to_dict_omits_id_when_none():
    sample = Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10)
    assert "id" not in sample.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "name": "Sample A", "avg_production_time": 2.5, "yield_rate": 0.9, "stock": 10}
    sample = Sample.from_dict(data)
    assert sample.sample_id == 1
    assert sample.name == "Sample A"
    assert sample.to_dict() == data


def test_raises_on_non_positive_avg_production_time():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=0, yield_rate=0.9, stock=10)


def test_raises_on_out_of_range_yield_rate():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=2.0, yield_rate=1.5, stock=10)


def test_raises_on_negative_stock():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=2.0, yield_rate=0.9, stock=-1)


def test_raises_on_zero_yield_rate():
    with pytest.raises(ValueError):
        Sample(name="X", avg_production_time=2.0, yield_rate=0, stock=10)
