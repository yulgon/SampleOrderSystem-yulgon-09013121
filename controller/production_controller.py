from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class ProductionController:
    MENU_TITLE = "생산 라인"
    MENU_OPTIONS = [(1, "생산 현황"), (2, "대기 주문 확인"), (3, "생산 완료 처리"), (4, "돌아가기")]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._show_current()
            elif choice == "2":
                self._show_pending()
            elif choice == "3":
                self._complete_current()
            elif choice == "4":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _describe(self, position, entry, expected_completion):
        order = self.orders.get(entry.order_id)
        sample = self.samples.get(entry.sample_id)
        return (
            f"순서={position}, 주문번호={entry.order_id}, 시료={sample.name}, "
            f"주문량={order.qty}, 부족분={entry.shortfall}, 실생산량={entry.actual_qty}, "
            f"예상완료={expected_completion}"
        )

    def _show_current(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("생산 중인 항목이 없습니다.")
            return
        head = queue[0]
        self.view.show_message(self._describe(1, head, head.total_time))

    def _show_pending(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("대기 중인 생산이 없습니다.")
            return
        cumulative = 0
        for position, entry in enumerate(queue, start=1):
            cumulative += entry.total_time
            self.view.show_message(self._describe(position, entry, cumulative))

    def _complete_current(self):
        queue = self.queue.list_all()
        if not queue:
            self.view.show_message("완료 처리할 생산이 없습니다.")
            return
        entry = queue[0]
        sample = self.samples.get(entry.sample_id)
        self.samples.update(sample.sample_id, {"stock": sample.stock + entry.shortfall})
        self.orders.update(entry.order_id, {"status": OrderStatus.CONFIRMED})
        self.queue.delete(entry.entry_id)
        self.view.show_success(
            f"생산 완료 처리: 주문ID={entry.order_id}, 재고 +{entry.shortfall}, "
            f"상태={OrderStatus.CONFIRMED}"
        )
