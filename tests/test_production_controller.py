import math

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from controller.production_controller import ProductionController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


def _setup_queued_order(base_dir, stock=2, yield_rate=0.5, avg_time=2.0, qty=10):
    samples = SampleRepository(base_dir=base_dir)
    orders = OrderRepository(base_dir=base_dir)
    queue = ProductionQueueRepository(base_dir=base_dir)

    sample = samples.create(
        Sample(name="Sample A", avg_production_time=avg_time, yield_rate=yield_rate, stock=stock)
    )
    order = orders.create(
        Order(sample_id=sample.sample_id, customer="Acme", qty=qty, status=OrderStatus.PRODUCING)
    )
    shortfall = qty - stock
    actual_qty = math.ceil(shortfall / yield_rate)
    total_time = avg_time * actual_qty
    entry = queue.create(
        ProductionQueueEntry(
            order_id=order.order_id, sample_id=sample.sample_id,
            shortfall=shortfall, actual_qty=actual_qty, total_time=total_time,
        )
    )
    return sample, order, entry


def test_current_status_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "생산 중인 항목이 없습니다." in view.messages


def test_current_status_shows_head_entry(tmp_path):
    sample, order, entry = _setup_queued_order(str(tmp_path))

    view = FakeView(inputs=["1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any(
        f"주문번호={order.order_id}" in m and f"예상완료={entry.total_time}" in m
        for m in view.messages
    )


def test_pending_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["2", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "대기 중인 생산이 없습니다." in view.messages


def test_pending_shows_cumulative_expected_completion(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample = samples.create(Sample(name="Sample A", avg_production_time=2.0, yield_rate=0.5, stock=0))
    order1 = orders.create(Order(sample_id=sample.sample_id, customer="A", qty=5, status=OrderStatus.PRODUCING))
    order2 = orders.create(Order(sample_id=sample.sample_id, customer="B", qty=5, status=OrderStatus.PRODUCING))
    queue.create(ProductionQueueEntry(
        order_id=order1.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))
    queue.create(ProductionQueueEntry(
        order_id=order2.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))

    view = FakeView(inputs=["2", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any("순서=1" in m and "예상완료=20.0" in m for m in view.messages)
    assert any("순서=2" in m and "예상완료=40.0" in m for m in view.messages)


def test_complete_current_shows_no_data_message_when_queue_empty(tmp_path):
    view = FakeView(inputs=["3", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "완료 처리할 생산이 없습니다." in view.messages


def test_complete_current_updates_stock_order_and_removes_entry(tmp_path):
    sample, order, entry = _setup_queued_order(str(tmp_path), stock=2, yield_rate=0.5, avg_time=2.0, qty=10)

    view = FakeView(inputs=["3", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    updated_sample = SampleRepository(base_dir=str(tmp_path)).get(sample.sample_id)
    updated_order = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    remaining_queue = ProductionQueueRepository(base_dir=str(tmp_path)).list_all()

    assert updated_sample.stock == 2 + entry.shortfall
    assert updated_order.status == OrderStatus.CONFIRMED
    assert remaining_queue == []


def test_completing_head_promotes_next_entry(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample = samples.create(Sample(name="Sample A", avg_production_time=2.0, yield_rate=0.5, stock=0))
    order1 = orders.create(Order(sample_id=sample.sample_id, customer="A", qty=5, status=OrderStatus.PRODUCING))
    order2 = orders.create(Order(sample_id=sample.sample_id, customer="B", qty=5, status=OrderStatus.PRODUCING))
    queue.create(ProductionQueueEntry(
        order_id=order1.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))
    queue.create(ProductionQueueEntry(
        order_id=order2.order_id, sample_id=sample.sample_id, shortfall=5, actual_qty=10, total_time=20.0
    ))

    view = FakeView(inputs=["3", "1", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()

    assert any(f"주문번호={order2.order_id}" in m for m in view.messages)


def test_invalid_menu_choice_shows_error(tmp_path):
    view = FakeView(inputs=["9", "4"])
    controller = ProductionController(view, base_dir=str(tmp_path))
    controller.run()
    assert "잘못된 입력입니다." in view.messages
