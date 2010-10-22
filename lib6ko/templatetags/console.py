from lib6ko import parameters as _P
import logging
_LOG = logging.getLogger("lib6ko.templatetags.console")

from . import ConsoleNodeBase

class ConsoleNode(ConsoleNodeBase):
    def __init__(self):
        super(ConsoleNode, self).__init__()
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
            self.protocol.execute_command(priv_cmd, expect_noecho=True)
            self.protocol.send_if_no_echo(priv_password)
            self.protocol.prompt(timeout=5)

    def tearDown(self):
        unpriv_cmd = self.protocol.require_param(_P.CONSOLE_PRIV_END)
        if unpriv_cmd:
            self.protocol.execute_command(unpriv_cmd)
            self.protocol.prompt()

class AllowOutputNode(ConsoleNodeBase):
    def __init__(self):
        self.oldval = False

    def setUp(self):
        self.oldval = self.protocol.allow_output
        self.protocol.allow_output = True

    def tearDown(self):
        self.protocol.allow_output = self.oldval

class SingleCommandNode(ConsoleNodeBase):
    def execute_text(self, text):
        return self.protocol.execute_command(text)
