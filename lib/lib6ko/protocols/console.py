import re
import logging
import pexpect
from cStringIO import StringIO

from lib6ko import parameters as _P
from lib6ko.protocol import Protocol

_LOG = logging.getLogger("protocols.console")

class ConsoleProtocol(Protocol):
    LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
    FAILURE = re.compile(r"failed", re.I)
    CLOSED = re.compile(r"closed", re.I)
    PROMPT = re.compile(r"(>|#)$")
    ROOT_PROMPT = re.compile(r"#")

    """ Console Protocol """
    def __init__(self, parameters):
        super(ConsoleProtocol, self).__init__(parameters)
        self.child = None
        self.EXIT_CMD = self.require_param(
            _P.CONSOLE_EXIT,
            default="exit",
            )
        self.priv_password = None
    
    @property
    def connected(self):
        return self.child is not None

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected")
            return

        _LOG.info("Disconnecting")
        self.child.sendline(self.EXIT_CMD)
        index = self.child.expect([
                self.CLOSED,
                pexpect.EOF,
                pexpect.TIMEOUT,
            ], timeout = 15 )

        self.child.close()
        self.child = None
        
    def execute_text(self, text):
        res = StringIO()
        self.child.logfile = res
        #Consume previous text
        if self.child.expect([self.PROMPT, pexpect.TIMEOUT], timeout=0) == 0:
            pass
            #res += self.child.match.group()

        #Send lines
        for line in text.splitlines():
            self.child.sendline(line)

        #Consume the output
        if self.child.expect([self.PROMPT, pexpect.TIMEOUT], timeout=0) == 0:
            pass
            #res += self.child.match.group()

        self.child.logfile = None
        return res.getvalue()

    def send_if_no_echo(self, text):
        if not self.child.getecho():
            self.child.sendline(text)
