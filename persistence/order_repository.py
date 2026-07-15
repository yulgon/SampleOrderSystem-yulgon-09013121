from model.order import Order
from persistence.repository import JsonRepository


class OrderRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("orders", base_dir=base_dir)

    def create(self, order):
        data = {k: v for k, v in order.to_dict().items() if k != "id"}
        record = self._repo.create(data)
        return Order.from_dict(record)

    def get(self, order_id):
        record = self._repo.get(order_id)
        return Order.from_dict(record) if record else None

    def list_all(self):
        return [Order.from_dict(record) for record in self._repo.list_all()]

    def update(self, order_id, changes):
        existing = self._repo.get(order_id)
        if existing is None:
            return None
        Order.from_dict({**existing, **changes})
        record = self._repo.update(order_id, changes)
        return Order.from_dict(record)

    def delete(self, order_id):
        return self._repo.delete(order_id)
