class FakeView:
    """Test double for ConsoleView: feeds canned inputs, records shown output."""

    def __init__(self, inputs=None):
        self._inputs = list(inputs or [])
        self.messages = []
        self.menus = []
        self.status_bars = []

    def show_message(self, message):
        self.messages.append(message)

    def show_error(self, message):
        self.messages.append(message)

    def show_success(self, message):
        self.messages.append(message)

    def show_menu(self, title, options):
        self.menus.append((title, options))

    def show_status_bar(self, registered_samples, total_stock, total_orders, waiting_lines):
        self.status_bars.append((registered_samples, total_stock, total_orders, waiting_lines))

    def get_input(self, prompt):
        return self._inputs.pop(0)
