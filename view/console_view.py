class ConsoleView:
    def show_message(self, message):
        print(message)

    def show_menu(self, title, options):
        print(f"\n=== {title} ===")
        for number, label in options:
            print(f"{number}. {label}")

    def get_input(self, prompt):
        return input(prompt)

    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        print(
            f"[상태] 등록시료: {registered_samples} | 총 재고: {total_stock} | "
            f"전체주문: {total_orders} | 대기중인 생산라인: {waiting_lines}"
        )
