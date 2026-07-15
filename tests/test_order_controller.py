import pytest

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from controller.order_controller import OrderController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


def _register_sample(base_dir, stock=10, yield_rate=0.9, avg_time=2.5):
    repo = SampleRepository(base_dir=base_dir)
    return repo.create(Sample(name="Sample A", avg_production_time=avg_time, yield_rate=yield_rate, stock=stock))


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


def _reserve_order(base_dir, sample_id, qty=5, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=OrderStatus.RESERVED))


def test_list_pending_shows_no_data_message_when_empty(tmp_path):
    view = FakeView(inputs=["1", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert "접수된 주문이 없습니다." in view.messages


def test_list_pending_shows_reserved_orders(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["1", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert any(f"ID={order.order_id}" in m for m in view.messages)


def test_approve_with_sufficient_stock_deducts_and_confirms(tmp_path):
    sample = _register_sample(str(tmp_path), stock=10)
    order = _reserve_order(str(tmp_path), sample.sample_id, qty=5)

    view = FakeView(inputs=["2", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    assert updated_order.status == OrderStatus.CONFIRMED
    assert updated_sample.stock == 5


def test_approve_with_insufficient_stock_queues_production(tmp_path):
    sample = _register_sample(str(tmp_path), stock=2, yield_rate=0.5, avg_time=2.0)
    order = _reserve_order(str(tmp_path), sample.sample_id, qty=10)

    view = FakeView(inputs=["2", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    queue_entries = ProductionQueueRepository(base_dir=str(tmp_path)).list_all()

    assert updated_order.status == OrderStatus.PRODUCING
    assert updated_sample.stock == 2
    assert len(queue_entries) == 1
    entry = queue_entries[0]
    assert entry.order_id == order.order_id
    assert entry.shortfall == 8
    assert entry.actual_qty == 16
    assert entry.total_time == 32.0


def test_reject_sets_rejected_status(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["3", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated_order.status == OrderStatus.REJECTED


def test_approve_retries_on_invalid_order_id(tmp_path):
    sample = _register_sample(str(tmp_path))
    order = _reserve_order(str(tmp_path), sample.sample_id)

    view = FakeView(inputs=["2", "999", str(order.order_id), "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()

    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated_order.status == OrderStatus.CONFIRMED
    assert any("유효한 접수 주문이 아닙니다." in m for m in view.messages)


def test_invalid_submenu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = OrderController(view, base_dir=str(tmp_path))
    controller.run_approve_reject()
    assert "잘못된 입력입니다." in view.messages


def test_zero_yield_rate_sample_cannot_be_registered(tmp_path):
    # Sample rejects yield_rate == 0 at construction, so _approve()'s
    # `shortfall / sample.yield_rate` division can never be reached with a
    # zero divisor: no sample with yield_rate == 0 can ever exist in the
    # repository for an insufficient-stock approval to look up.
    with pytest.raises(ValueError):
        Sample(name="Zero Yield", avg_production_time=2.0, yield_rate=0, stock=10)
