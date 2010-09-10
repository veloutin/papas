from lib6ko import parameters as _P

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
        priv_cmd = self.protocol.require_param(_P.CONSOLE_PRIV_MODE)
        priv_password = self.protocol.require_param(
            _P.CONSOLE_PRIV_PASSWORD,
            default=self.protocol.priv_password,
            )
        if priv_cmd:
            self.protocol.execute_text(priv_cmd)
            self.protocol.send_if_no_echo(priv_password)

    def tearDown(self):
        unpriv_cmd = self.protocol.require_param(_P.CONSOLE_PRIV_END)
        if unpriv_cmd:
            self.protocol.execute_text(unpriv_cmd)

class AllowOutputNode(ConsoleNodeBase):
    def setUp(self):
        self.protocol.allow_output = True

    def tearDown(self):
        self.protocol.allow_output = False
