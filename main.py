from view.console_view import ConsoleView
from controller.sample_controller import SampleController
from controller.order_controller import OrderController


def main():
    view = ConsoleView()
    sample_controller = SampleController(view)
    order_controller = OrderController(view)

    while True:
        view.show_menu(
            "메인 메뉴",
            [(0, "종료"), (1, "시료 관리"), (2, "시료 주문"), (3, "주문 (승인/거절)")],
        )
        choice = view.get_input("메뉴 번호를 입력하세요: ")

        if choice == "0":
            return
        elif choice == "1":
            sample_controller.run()
        elif choice == "2":
            order_controller.run_reserve()
        elif choice == "3":
            order_controller.run_approve_reject()
        else:
            view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
