from model.sample import Sample
from model.order import Order, OrderStatus
from controller.monitor_controller import MonitorController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _make_sample(base_dir, name="Sample A", stock=10):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name=name, avg_production_time=2.0, yield_rate=0.9, stock=stock))


def _make_order(base_dir, sample_id, qty=5, status=OrderStatus.RESERVED, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=status))


def test_order_volume_counts_each_status_and_excludes_rejected(tmp_path):
    sample = _make_sample(str(tmp_path))
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.RESERVED)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.CONFIRMED)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.PRODUCING)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.RELEASE)
    _make_order(str(tmp_path), sample.sample_id, status=OrderStatus.REJECTED)

    view = FakeView(inputs=["1", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()

    assert any("RESERVED: 1건" in m for m in view.messages)
    assert any("CONFIRMED: 1건" in m for m in view.messages)
    assert any("PRODUCING: 1건" in m for m in view.messages)
    assert any("RELEASE: 1건" in m for m in view.messages)
    assert not any("REJECTED" in m for m in view.messages)


def test_order_volume_shows_zero_counts_when_no_orders(tmp_path):
    view = FakeView(inputs=["1", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("RESERVED: 0건" in m for m in view.messages)


def test_stock_levels_shows_no_data_message_when_no_samples(tmp_path):
    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert "등록된 시료가 없습니다." in view.messages


def test_stock_levels_shows_surplus_when_stock_covers_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=10)
    _make_order(str(tmp_path), sample.sample_id, qty=5, status=OrderStatus.RESERVED)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("여유" in m for m in view.messages)


def test_stock_levels_shows_shortage_when_stock_below_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=3)
    _make_order(str(tmp_path), sample.sample_id, qty=5, status=OrderStatus.PRODUCING)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("부족" in m for m in view.messages)


def test_stock_levels_shows_depleted_when_stock_is_zero(tmp_path):
    _make_sample(str(tmp_path), stock=0)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("고갈" in m for m in view.messages)


def test_stock_levels_ignores_confirmed_and_release_orders_for_demand(tmp_path):
    sample = _make_sample(str(tmp_path), stock=5)
    _make_order(str(tmp_path), sample.sample_id, qty=100, status=OrderStatus.CONFIRMED)
    _make_order(str(tmp_path), sample.sample_id, qty=100, status=OrderStatus.RELEASE)

    view = FakeView(inputs=["2", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert any("여유" in m for m in view.messages)


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "3"])
    controller = MonitorController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
