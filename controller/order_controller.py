from model.order import Order, OrderStatus
from persistence.order_repository import OrderRepository
from persistence.sample_repository import SampleRepository


class OrderController:
    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)

    def run_reserve(self):
        sample = self._prompt_existing_sample()
        customer = self.view.get_input("고객명: ")
        qty = self._prompt_qty()
        order = self.orders.create(
            Order(sample_id=sample.sample_id, customer=customer, qty=qty, status=OrderStatus.RESERVED)
        )
        self.view.show_message(
            f"주문 접수 완료: ID={order.order_id}, 시료ID={order.sample_id}, "
            f"고객명={order.customer}, 수량={order.qty}, 상태={order.status}"
        )

    def _prompt_existing_sample(self):
        while True:
            raw = self.view.get_input("시료 ID: ")
            try:
                sample_id = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            sample = self.samples.get(sample_id)
            if sample is None:
                self.view.show_message("존재하지 않는 시료 ID입니다.")
                continue
            return sample

    def _prompt_qty(self):
        while True:
            raw = self.view.get_input("주문 수량: ")
            try:
                qty = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if qty <= 0:
                self.view.show_message("주문 수량은 0보다 커야 합니다.")
                continue
            return qty
