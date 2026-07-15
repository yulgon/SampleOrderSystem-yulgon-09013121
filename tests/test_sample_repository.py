from model.sample import Sample
from persistence.sample_repository import SampleRepository


def _make_sample(name="Sample A", stock=10):
    return Sample(name=name, avg_production_time=2.5, yield_rate=0.9, stock=stock)


def test_create_returns_sample_with_assigned_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert isinstance(created, Sample)
    assert created.sample_id == 1
    assert created.name == "Sample A"


def test_get_returns_matching_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert repo.get(created.sample_id) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_samples_in_order(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(_make_sample(name="A"))
    repo.create(_make_sample(name="B"))
    assert [s.name for s in repo.list_all()] == ["A", "B"]


def test_update_merges_fields_and_returns_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample(stock=5))
    updated = repo.update(created.sample_id, {"stock": 20})
    assert updated.stock == 20
    assert updated.name == "Sample A"


def test_update_returns_none_for_missing_id(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    assert repo.update(999, {"stock": 20}) is None


def test_delete_removes_sample(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample())
    assert repo.delete(created.sample_id) is True
    assert repo.get(created.sample_id) is None
