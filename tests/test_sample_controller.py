from model.sample import Sample
from controller.sample_controller import SampleController
from persistence.sample_repository import SampleRepository
from tests.fakes import FakeView


def test_register_creates_sample_and_shows_assigned_id(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert len(samples) == 1
    assert samples[0].name == "Sample A"
    assert any("ID=1" in m for m in view.messages)


def test_register_retries_on_non_numeric_avg_production_time(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "abc", "2.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].avg_production_time == 2.5
    assert any("숫자를 입력해주세요" in m for m in view.messages)


def test_register_retries_on_out_of_range_yield_rate(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "1.5", "0.9", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].yield_rate == 0.9


def test_register_retries_on_negative_stock(tmp_path):
    view = FakeView(inputs=["1", "Sample A", "2.5", "0.9", "-1", "10", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()

    samples = SampleRepository(base_dir=str(tmp_path)).list_all()
    assert samples[0].stock == 10


def test_list_shows_no_data_message_when_empty(tmp_path):
    view = FakeView(inputs=["2", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "등록된 시료가 없습니다." in view.messages


def test_list_shows_registered_samples(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))

    view = FakeView(inputs=["2", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("Sample A" in m for m in view.messages)


def test_search_finds_matching_sample_only(tmp_path):
    repo = SampleRepository(base_dir=str(tmp_path))
    repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))
    repo.create(Sample(name="Other B", avg_production_time=1.0, yield_rate=0.8, stock=5))

    view = FakeView(inputs=["3", "Sample", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("Sample A" in m for m in view.messages)
    assert not any("Other B" in m for m in view.messages)


def test_search_shows_no_match_message(tmp_path):
    view = FakeView(inputs=["3", "Nonexistent", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "일치하는 시료가 없습니다." in view.messages


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = SampleController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
