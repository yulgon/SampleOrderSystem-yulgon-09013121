from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.release_controller import ReleaseController
from controller.monitor_controller import MonitorController
from controller.app_controller import AppController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)
    production_controller = ProductionController(view)
    release_controller = ReleaseController(view)
    monitor_controller = MonitorController(view)

    app = AppController(
        view,
        sample_controller,
        order_controller,
        monitor_controller,
        production_controller,
        release_controller,
    )
    app.run()


if __name__ == "__main__":
    main()
