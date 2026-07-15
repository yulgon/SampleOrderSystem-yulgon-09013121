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


def test_update_does_not_persist_invalid_changes(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    created = repo.create(_make_sample(stock=5))
    try:
        repo.update(created.sample_id, {"stock": -1})
        assert False, "expected ValueError"
    except ValueError:
        pass
    fresh_repo = SampleRepository(base_dir=str(tmp_path))
    assert fresh_repo.get(created.sample_id) == created


def test_create_ignores_preset_id_and_assigns_a_fresh_one(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(_make_sample())
    preset = Sample(
        name="Sample B",
        avg_production_time=1.0,
        yield_rate=0.5,
        stock=1,
        sample_id=1,
    )
    second = repo.create(preset)
    assert second.sample_id == 2
    all_samples = repo.list_all()
    assert len(all_samples) == 2
    assert {s.sample_id for s in all_samples} == {1, 2}
