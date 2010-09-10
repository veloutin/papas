import re
import logging
import pexpect
from cStringIO import StringIO

from lib6ko import parameters as _P
from lib6ko.protocol import Protocol
from lib6ko.architecture import Architecture

_LOG = logging.getLogger("protocols.console")

class ConsoleProtocol(Protocol):

    """ Console Protocol """
    def __init__(self, parameters):
        super(ConsoleProtocol, self).__init__(parameters)
        self.arch = Architecture()
        self.child = None
        self.EXIT_CMD = self.require_param(
            _P.CONSOLE_EXIT,
            default="exit",
            )
        self.priv_password = None
    
    @property
    def allow_output(self):
        return self.arch.console.allow_output

    @allow_output.setter
    def allow_output(self, value):
        self.arch.console.allow_output = value

    @property
    def child(self):
        return self.arch.console.child

    @child.setter
    def child(self, value):
        self.arch.console.child = value

    @child.deleter
    def child(self):
        del self.arch.console.child

    @property
    def connected(self):
        return self.child is not None

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected")
            return

        _LOG.info("Disconnecting")
        self.arch.console.prompt()
        #Do not use execute_command as it will raise EOF
        self.child.sendline(self.EXIT_CMD)
        index = self.child.expect([
                self.arch.console.CLOSED,
                pexpect.EOF,
                pexpect.TIMEOUT,
            ], timeout = 15 )

        self.child.close()
        self.child = None
    
    def execute_text(self, text):
        for line in text.splitlines():
            self.arch.console.execute_command(line)

        return self.arch.console.consume_output()

    def send_if_no_echo(self, text):
        self.arch.console.send_password(text)
