from model.order import OrderStatus
from persistence.order_repository import OrderRepository


class ReleaseController:
    def __init__(self, view, base_dir="data"):
        self.view = view
        self.orders = OrderRepository(base_dir=base_dir)

    def run(self):
        order = self._prompt_confirmed_order()
        self.orders.update(order.order_id, {"status": OrderStatus.RELEASE})
        self.view.show_success(
            f"출고 완료: 주문ID={order.order_id}, 상태={OrderStatus.RELEASE}"
        )

    def _prompt_confirmed_order(self):
        while True:
            raw = self.view.get_input("주문 ID: ")
            try:
                order_id = int(raw)
            except ValueError:
                self.view.show_error("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.CONFIRMED:
                self.view.show_error("출고 가능한(CONFIRMED) 주문이 아닙니다.")
                continue
            return order
