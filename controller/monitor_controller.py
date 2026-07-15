from model.order import OrderStatus
from persistence.order_repository import OrderRepository
from persistence.sample_repository import SampleRepository


class MonitorController:
    MENU_TITLE = "모니터링"
    MENU_OPTIONS = [(1, "주문량 확인"), (2, "재고량 확인"), (3, "돌아가기")]
    VOLUME_STATUSES = (
        OrderStatus.RESERVED,
        OrderStatus.CONFIRMED,
        OrderStatus.PRODUCING,
        OrderStatus.RELEASE,
    )
    OUTSTANDING_STATUSES = (OrderStatus.RESERVED, OrderStatus.PRODUCING)

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.samples = SampleRepository(base_dir=base_dir)
        self.orders = OrderRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._show_order_volume()
            elif choice == "2":
                self._show_stock_levels()
            elif choice == "3":
                return
            else:
                self.view.show_error("잘못된 입력입니다.")

    def _show_order_volume(self):
        orders = self.orders.list_all()
        for status in self.VOLUME_STATUSES:
            count = sum(1 for order in orders if order.status == status)
            self.view.show_message(f"{status}: {count}건")

    def _show_stock_levels(self):
        samples = self.samples.list_all()
        if not samples:
            self.view.show_message("등록된 시료가 없습니다.")
            return
        orders = self.orders.list_all()
        for sample in samples:
            demand = sum(
                order.qty for order in orders
                if order.sample_id == sample.sample_id
                and order.status in self.OUTSTANDING_STATUSES
            )
            if sample.stock == 0:
                label = "고갈"
            elif sample.stock >= demand:
                label = "여유"
            else:
                label = "부족"
            self.view.show_message(
                f"시료={sample.name}, 재고={sample.stock}, 상태={label}"
            )
