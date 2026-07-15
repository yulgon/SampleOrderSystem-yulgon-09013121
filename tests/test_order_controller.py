from model.sample import Sample
from model.order import OrderStatus
from controller.order_controller import OrderController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _register_sample(base_dir):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name="Sample A", avg_production_time=2.5, yield_rate=0.9, stock=10))


def test_run_reserve_creates_order_with_reserved_status(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1
    assert orders[0].sample_id == sample.sample_id
    assert orders[0].customer == "Acme"
    assert orders[0].qty == 5
    assert orders[0].status == OrderStatus.RESERVED
    assert any("ID=1" in m for m in view.messages)


def test_run_reserve_retries_on_missing_sample_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=["999", str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1
    assert orders[0].sample_id == sample.sample_id
    assert any("존재하지 않는 시료 ID입니다." in m for m in view.messages)


def test_run_reserve_retries_on_non_numeric_sample_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=["abc", str(sample.sample_id), "Acme", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert len(orders) == 1


def test_run_reserve_retries_on_non_numeric_qty(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "abc", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert orders[0].qty == 5


def test_run_reserve_retries_on_non_positive_qty(tmp_path):
    sample = _register_sample(str(tmp_path))
    view = FakeView(inputs=[str(sample.sample_id), "Acme", "0", "5"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_reserve()

    orders = OrderRepository(base_dir=str(tmp_path)).list_all()
    assert orders[0].qty == 5
