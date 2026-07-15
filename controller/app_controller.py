from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from persistence.sample_repository import SampleRepository


class AppController:
    MENU_TITLE = "메인 메뉴"
    MENU_OPTIONS = [
        (1, "시료 관리"),
        (2, "시료 주문"),
        (3, "주문 (승인/거절)"),
        (4, "모니터링"),
        (5, "출고 처리"),
        (6, "생산 라인"),
        (7, "종료"),
    ]

    def __init__(self, view, sample_controller, order_controller, monitor_controller,
                 production_controller, release_controller, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)
        self.queue = ProductionQueueRepository(base_dir=base_dir)
        self._handlers = {
            1: sample_controller.run,
            2: order_controller.run_reserve,
            3: order_controller.run_approve_reject,
            4: monitor_controller.run,
            5: release_controller.run,
            6: production_controller.run,
        }

    def run(self):
        while True:
            self._show_status_bar()
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "7":
                self.view.show_message("프로그램을 종료합니다.")
                return

            try:
                menu_number = int(choice)
            except ValueError:
                self.view.show_error("잘못된 입력입니다.")
                continue

            handler = self._handlers.get(menu_number)
            if handler is None:
                self.view.show_error("잘못된 입력입니다.")
                continue

            handler()

    def _show_status_bar(self):
        samples = self.samples.list_all()
        orders = self.orders.list_all()
        self.view.show_status_bar(
            registered_samples=len(samples),
            total_stock=sum(sample.stock for sample in samples),
            total_orders=sum(1 for order in orders if order.status != OrderStatus.REJECTED),
            waiting_lines=len(self.queue.list_all()),
        )
