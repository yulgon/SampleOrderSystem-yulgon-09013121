import math

from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class OrderController:
    APPROVE_MENU_TITLE = "주문 (승인/거절)"
    APPROVE_MENU_OPTIONS = [
        (1, "접수된 주문 목록"),
        (2, "주문 승인"),
        (3, "주문 거절"),
        (4, "돌아가기"),
    ]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)

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

    def run_approve_reject(self):
        while True:
            self.view.show_menu(self.APPROVE_MENU_TITLE, self.APPROVE_MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._list_pending()
            elif choice == "2":
                self._approve()
            elif choice == "3":
                self._reject()
            elif choice == "4":
                return
            else:
                self.view.show_message("잘못된 입력입니다.")

    def _list_pending(self):
        pending = [o for o in self.orders.list_all() if o.status == OrderStatus.RESERVED]
        if not pending:
            self.view.show_message("접수된 주문이 없습니다.")
            return
        for order in pending:
            self.view.show_message(
                f"ID={order.order_id}, 시료ID={order.sample_id}, "
                f"고객명={order.customer}, 수량={order.qty}"
            )

    def _prompt_pending_order(self):
        while True:
            raw = self.view.get_input("주문 ID: ")
            try:
                order_id = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            order = self.orders.get(order_id)
            if order is None or order.status != OrderStatus.RESERVED:
                self.view.show_message("유효한 접수 주문이 아닙니다.")
                continue
            return order

    def _approve(self):
        order = self._prompt_pending_order()
        sample = self.samples.get(order.sample_id)

        if sample.stock >= order.qty:
            self.samples.update(sample.sample_id, {"stock": sample.stock - order.qty})
            self.orders.update(order.order_id, {"status": OrderStatus.CONFIRMED})
            self.view.show_message(
                f"승인 완료 (재고 차감): ID={order.order_id}, 상태={OrderStatus.CONFIRMED}"
            )
        else:
            shortfall = order.qty - sample.stock
            actual_qty = math.ceil(shortfall / sample.yield_rate)
            total_time = sample.avg_production_time * actual_qty
            self.queue.create(
                ProductionQueueEntry(
                    order_id=order.order_id,
                    sample_id=sample.sample_id,
                    shortfall=shortfall,
                    actual_qty=actual_qty,
                    total_time=total_time,
                )
            )
            self.orders.update(order.order_id, {"status": OrderStatus.PRODUCING})
            self.view.show_message(
                f"재고 부족 - 생산 등록: 주문ID={order.order_id}, 부족분={shortfall}, "
                f"실생산량={actual_qty}, 총생산시간={total_time}"
            )

    def _reject(self):
        order = self._prompt_pending_order()
        self.orders.update(order.order_id, {"status": OrderStatus.REJECTED})
        self.view.show_message(
            f"주문 거절 완료: ID={order.order_id}, 상태={OrderStatus.REJECTED}"
        )
