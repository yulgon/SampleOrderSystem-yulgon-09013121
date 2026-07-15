from model.order import Order, OrderStatus
from controller.release_controller import ReleaseController
from persistence.order_repository import OrderRepository
from tests.fakes import FakeView


def _make_order(base_dir, status=OrderStatus.CONFIRMED, sample_id=1, qty=5, customer="Acme"):
    repo = OrderRepository(base_dir=base_dir)
    return repo.create(Order(sample_id=sample_id, customer=customer, qty=qty, status=status))


def test_release_transitions_confirmed_order_to_release(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=[str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert any(f"주문ID={order.order_id}" in m for m in view.messages)


def test_release_retries_on_missing_order_id(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=["999", str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert any("출고 가능한(CONFIRMED) 주문이 아닙니다." in m for m in view.messages)


def test_release_retries_on_non_confirmed_order(tmp_path):
    pending_order = _make_order(str(tmp_path), status=OrderStatus.RESERVED)
    confirmed_order = _make_order(str(tmp_path), status=OrderStatus.CONFIRMED)
    view = FakeView(inputs=[str(pending_order.order_id), str(confirmed_order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(confirmed_order.order_id)
    assert updated.status == OrderStatus.RELEASE


def test_release_retries_on_non_numeric_order_id(tmp_path):
    order = _make_order(str(tmp_path))
    view = FakeView(inputs=["abc", str(order.order_id)])
    controller = ReleaseController(view, base_dir=str(tmp_path))
    controller.run()

    updated = OrderRepository(base_dir=str(tmp_path)).get(order.order_id)
    assert updated.status == OrderStatus.RELEASE
