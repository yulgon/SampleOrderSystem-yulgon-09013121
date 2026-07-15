from view.console_view import ConsoleView
from controller.sample_controller import SampleController


def main():
    view = ConsoleView()
    controller = SampleController(view)
    controller.run()


if __name__ == "__main__":
    main()
