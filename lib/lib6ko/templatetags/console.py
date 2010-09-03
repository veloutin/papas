from . import ConsoleNodeBase

class ConsoleNode(ConsoleNodeBase):
    def __init__(self):
        self._owns_connection = False

    def setUp(self):
        if not self.protocol.connected:
            self.protocol.connect()
            self._owns_connection = True

    def tearDown(self):
        if self._owns_connection:
            self.protocol.disconnect()

class RootConsoleNode(ConsoleNodeBase):
    def setUp(self):
        self.protocol.execute_text("enable")
        self.protocol.send_if_no_echo("Cisco")

    def tearDown(self):
        self.protocol.execute_text("disable")
