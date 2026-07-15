from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_queue_entry import ProductionQueueEntry
from controller.app_controller import AppController
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository
from persistence.production_queue_repository import ProductionQueueRepository
from tests.fakes import FakeView


class RecordingHandler:
    def __init__(self):
        self.calls = 0

    def run(self):
        self.calls += 1

    run_reserve = run
    run_approve_reject = run


class OrderStub:
    def __init__(self):
        self.reserve_calls = 0
        self.approve_reject_calls = 0

    def run_reserve(self):
        self.reserve_calls += 1

    def run_approve_reject(self):
        self.approve_reject_calls += 1


def _make_controller(tmp_path, inputs, order=None):
    sample = RecordingHandler()
    order = order or RecordingHandler()
    monitor = RecordingHandler()
    production = RecordingHandler()
    release = RecordingHandler()
    view = FakeView(inputs=inputs)
    controller = AppController(
        view, sample, order, monitor, production, release, base_dir=str(tmp_path)
    )
    return controller, view, sample, order, monitor, production, release


def test_selecting_sample_menu_dispatches_to_sample_controller(tmp_path):
    controller, view, sample, *_ = _make_controller(tmp_path, ["1", "7"])
    controller.run()
    assert sample.calls == 1


def test_selecting_exit_stops_the_loop_without_dispatching(tmp_path):
    controller, view, sample, *_ = _make_controller(tmp_path, ["7"])
    controller.run()
    assert sample.calls == 0
    assert "종료" in view.messages[-1]


def test_invalid_menu_number_shows_error_and_reprompts(tmp_path):
    controller, view, *_ = _make_controller(tmp_path, ["99", "7"])
    controller.run()
    assert "잘못된 입력입니다." in view.messages


def test_non_numeric_input_shows_error_and_reprompts(tmp_path):
    controller, view, *_ = _make_controller(tmp_path, ["abc", "7"])
    controller.run()
    assert "잘못된 입력입니다." in view.messages


def test_selecting_order_menu_dispatches_to_run_reserve(tmp_path):
    order = OrderStub()
    controller, view, *_ = _make_controller(tmp_path, ["2", "7"], order=order)
    controller.run()
    assert order.reserve_calls == 1
    assert order.approve_reject_calls == 0


def test_selecting_approve_reject_menu_dispatches_to_run_approve_reject(tmp_path):
    order = OrderStub()
    controller, view, *_ = _make_controller(tmp_path, ["3", "7"], order=order)
    controller.run()
    assert order.approve_reject_calls == 1


def test_status_bar_reflects_real_repository_state(tmp_path):
    samples = SampleRepository(base_dir=str(tmp_path))
    orders = OrderRepository(base_dir=str(tmp_path))
    queue = ProductionQueueRepository(base_dir=str(tmp_path))

    sample1 = samples.create(Sample(name="A", avg_production_time=2.0, yield_rate=0.9, stock=5))
    samples.create(Sample(name="B", avg_production_time=2.0, yield_rate=0.9, stock=3))
    order1 = orders.create(
        Order(sample_id=sample1.sample_id, customer="X", qty=1, status=OrderStatus.RESERVED)
    )
    orders.create(
        Order(sample_id=sample1.sample_id, customer="Y", qty=1, status=OrderStatus.REJECTED)
    )
    queue.create(
        ProductionQueueEntry(
            order_id=order1.order_id, sample_id=sample1.sample_id,
            shortfall=1, actual_qty=2, total_time=4.0,
        )
    )

    controller, view, *_ = _make_controller(tmp_path, ["7"])
    controller.run()

    # 2 samples registered, stock 5+3=8, 1 non-rejected order, 1 queue entry
    assert view.status_bars[0] == (2, 8, 1, 1)
