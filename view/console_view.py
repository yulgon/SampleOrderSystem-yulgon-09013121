import sys


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"


def _enable_windows_ansi():
    if sys.platform != "win32":
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


class ConsoleView:
    def __init__(self):
        _enable_windows_ansi()

    def show_message(self, message):
        print(message)

    def show_success(self, message):
        print(f"{Color.GREEN}{message}{Color.RESET}")

    def show_error(self, message):
        print(f"{Color.RED}{message}{Color.RESET}")

    def show_menu(self, title, options):
        print(f"\n{Color.CYAN}{Color.BOLD}=== {title} ==={Color.RESET}")
        for number, label in options:
            print(f"{number}. {label}")

    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        print(
            f"{Color.CYAN}[상태] 등록시료: {registered_samples} | 총 재고: {total_stock} | "
            f"전체주문: {total_orders} | 대기중인 생산라인: {waiting_lines}{Color.RESET}"
        )

    def show_banner(self):
        print(f"{Color.CYAN}{Color.BOLD}")
        print("=" * 50)
        print("   S-Semi SampleOrderSystem")
        print("=" * 50)
        print(Color.RESET)

    def get_input(self, prompt):
        return input(prompt)
