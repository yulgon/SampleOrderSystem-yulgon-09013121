class ConsoleView:
    def show_message(self, message):
        print(message)

    def show_menu(self, title, options):
        print(f"\n=== {title} ===")
        for number, label in options:
            print(f"{number}. {label}")

    def get_input(self, prompt):
        return input(prompt)
