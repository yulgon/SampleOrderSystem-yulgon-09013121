class FakeView:
    """Test double for ConsoleView: feeds canned inputs, records shown output."""

    def __init__(self, inputs=None):
        self._inputs = list(inputs or [])
        self.messages = []
        self.menus = []

    def show_message(self, message):
        self.messages.append(message)

    def show_menu(self, title, options):
        self.menus.append((title, options))

    def get_input(self, prompt):
        return self._inputs.pop(0)
