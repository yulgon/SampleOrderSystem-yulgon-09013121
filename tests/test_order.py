import pytest

from model.order import Order, OrderStatus


def test_order_status_values():
    assert OrderStatus.RESERVED == "RESERVED"
    assert OrderStatus.REJECTED == "REJECTED"
    assert OrderStatus.PRODUCING == "PRODUCING"
    assert OrderStatus.CONFIRMED == "CONFIRMED"
    assert OrderStatus.RELEASE == "RELEASE"
    assert set(OrderStatus.ALL) == {"RESERVED", "REJECTED", "PRODUCING", "CONFIRMED", "RELEASE"}


def test_to_dict_includes_id_when_present():
    order = Order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED, order_id=1)
    assert order.to_dict() == {
        "id": 1,
        "sample_id": 1,
        "customer": "Acme",
        "qty": 5,
        "status": "RESERVED",
    }


def test_to_dict_omits_id_when_none():
    order = Order(sample_id=1, customer="Acme", qty=5, status=OrderStatus.RESERVED)
    assert "id" not in order.to_dict()


def test_from_dict_round_trips():
    data = {"id": 1, "sample_id": 1, "customer": "Acme", "qty": 5, "status": "RESERVED"}
    order = Order.from_dict(data)
    assert order.order_id == 1
    assert order.to_dict() == data


def test_raises_on_non_positive_qty():
    with pytest.raises(ValueError):
        Order(sample_id=1, customer="Acme", qty=0, status=OrderStatus.RESERVED)


def test_raises_on_invalid_status():
    with pytest.raises(ValueError):
        Order(sample_id=1, customer="Acme", qty=5, status="NOT_A_STATUS")
