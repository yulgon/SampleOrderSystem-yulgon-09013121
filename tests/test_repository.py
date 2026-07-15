from persistence.repository import JsonRepository


def test_create_assigns_sequential_id_and_returns_record(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    record = repo.create({"name": "Sample A"})
    assert record["id"] == 1

    second = repo.create({"name": "Sample B"})
    assert second["id"] == 2


def test_get_returns_matching_record(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    created = repo.create({"name": "Sample A"})
    assert repo.get(created["id"]) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_records(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    repo.create({"name": "Sample B"})
    assert repo.list_all() == [
        {"id": 1, "name": "Sample A"},
        {"id": 2, "name": "Sample B"},
    ]


def test_list_all_returns_empty_list_when_no_file_exists(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.list_all() == []


def test_create_persists_across_repository_instances(tmp_path):
    repo1 = JsonRepository("samples", base_dir=str(tmp_path))
    repo1.create({"name": "Sample A"})
    repo2 = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo2.list_all() == [{"id": 1, "name": "Sample A"}]


def test_update_merges_fields_and_persists(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A", "stock": 10})
    updated = repo.update(1, {"stock": 20})
    assert updated == {"id": 1, "name": "Sample A", "stock": 20}
    assert repo.get(1) == {"id": 1, "name": "Sample A", "stock": 20}


def test_update_returns_none_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    assert repo.update(999, {"stock": 20}) is None


def test_delete_removes_record_and_returns_true(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    assert repo.delete(1) is True
    assert repo.get(1) is None
    assert repo.list_all() == []


def test_delete_returns_false_for_missing_id(tmp_path):
    repo = JsonRepository("samples", base_dir=str(tmp_path))
    repo.create({"name": "Sample A"})
    assert repo.delete(999) is False
    assert repo.list_all() == [{"id": 1, "name": "Sample A"}]
