from model.order import OrderStatus
from controller.app_controller import AppController
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.monitor_controller import MonitorController
from controller.production_controller import ProductionController
from controller.release_controller import ReleaseController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


def test_full_order_lifecycle_through_app_controller(tmp_path):
    base_dir = str(tmp_path)

    inputs = [
        # -- Menu 1: 시료 관리 --
        "1",            # main menu: 시료 관리
        "1",            #   sample menu: 시료 등록
        "Sample A",     #     시료명
        "10",           #     평균 생산시간
        "0.5",          #     수율
        "3",            #     현재 재고
        "4",            #   sample menu: 돌아가기

        # -- Menu 2: 시료 주문 (reserve qty=10 against stock=3) --
        "2",            # main menu: 시료 주문
        "1",            #   시료 ID
        "Customer A",   #   고객명
        "10",           #   주문 수량

        # -- Menu 3: 주문 (승인/거절) --
        "3",            # main menu: 주문 승인/거절
        "2",            #   approve menu: 주문 승인
        "1",            #     주문 ID
        "4",            #   approve menu: 돌아가기

        # -- Menu 6: 생산 라인 (complete production) --
        "6",            # main menu: 생산 라인
        "3",            #   생산 완료 처리
        "4",            #   production menu: 돌아가기

        # -- Menu 5: 출고 처리 --
        "5",            # main menu: 출고 처리
        "1",            #   주문 ID

        # -- Menu 4: 모니터링 --
        "4",            # main menu: 모니터링
        "1",            #   주문량 확인
        "2",            #   재고량 확인
        "3",            #   monitor menu: 돌아가기

        # -- Exit --
        "7",
    ]

    view = FakeView(inputs=inputs)
    sample_controller = SampleController(view, base_dir=base_dir)
    order_controller = OrderController(view, base_dir=base_dir)
    monitor_controller = MonitorController(view, base_dir=base_dir)
    production_controller = ProductionController(view, base_dir=base_dir)
    release_controller = ReleaseController(view, base_dir=base_dir)

    app = AppController(
        view,
        sample_controller,
        order_controller,
        monitor_controller,
        production_controller,
        release_controller,
        base_dir=base_dir,
    )

    app.run()

    samples = SampleRepository(base_dir=base_dir)
    orders = OrderRepository(base_dir=base_dir)
    queue = ProductionQueueRepository(base_dir=base_dir)

    sample = samples.get(1)
    order = orders.get(1)

    # original stock 3, shortfall 10-3=7, restored on production completion
    assert sample.stock == 10
    assert order.status == OrderStatus.RELEASE
    assert queue.list_all() == []
