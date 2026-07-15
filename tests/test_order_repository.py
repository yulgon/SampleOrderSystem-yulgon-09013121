from model.order import Order, OrderStatus
from persistence.order_repository import OrderRepository


def _make_order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED):
    return Order(sample_id=sample_id, customer=customer, qty=qty, status=status)


def test_create_returns_order_with_assigned_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert isinstance(created, Order)
    assert created.order_id == 1
    assert created.status == OrderStatus.RESERVED


def test_get_returns_matching_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert repo.get(created.order_id) == created


def test_get_returns_none_for_missing_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    assert repo.get(999) is None


def test_list_all_returns_all_orders_in_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    repo.create(_make_order(customer="Acme"))
    repo.create(_make_order(customer="Globex"))
    assert [o.customer for o in repo.list_all()] == ["Acme", "Globex"]


def test_update_changes_status_and_returns_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    updated = repo.update(created.order_id, {"status": OrderStatus.CONFIRMED})
    assert updated.status == OrderStatus.CONFIRMED
    assert updated.customer == "Acme"


def test_update_returns_none_for_missing_id(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    assert repo.update(999, {"status": OrderStatus.REJECTED}) is None


def test_delete_removes_order(tmp_path):
    repo = OrderRepository(base_dir=str(tmp_path))
    created = repo.create(_make_order())
    assert repo.delete(created.order_id) is True
    assert repo.get(created.order_id) is None
