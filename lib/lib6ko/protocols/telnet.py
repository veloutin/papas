import pexpect, re
import socket
import logging
from gettext import gettext as _

_LOG = logging.getLogger("protocols.telnet")

from ..protocol import ConsoleProtocol

LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
FAILURE = re.compile(r"failed", re.I)
CLOSED = re.compile(r"closed", re.I)
PROMPT = re.compile(r"(>|#)")
ROOT_PROMPT = re.compile(r"#")

class Telnet(ConsoleProtocol):
    def __init__(self, parameters):
        self._child = None
        self._host = self._require(parameters, "ap::ipv4Address")
        self._username = self._require(parameters, "param::Telnet::Username")
        self._password = self._require(parameters, "param::Telnet::Password")

        self.connect()

    def connect(self):
        _LOG.info(_("Attempting to connect to {0._username}@{0._host}").format(self))
        try:
            target = socket.gethostbyname(self._host)
        except socket.gaierror as e:
            _LOG.error(str(e))
            raise PermanentFailure("Invalid host: " + e.strerror)

        self._child = c = pexpect.spawn("telnet %s" % target)

        index = c.expect([
                LOGIN_PROMPT,
                pexpect.TIMEOUT,
                pexpect.EOF,
            ], timeout=30)

        if index == 0:
            c.sendline(self._username) #Make sure it is the right end of line CR/LF?
        else:
            _LOG.info("Unable to get prompt")
            c.terminate()
            self._child = None
            raise TemporaryFailure("Unable to connect")

        c.waitnoecho( 30 )
        c.sendline(self._password)

        index = c.expect([
                PROMPT,
                LOGIN_PROMPT,
                FAILURE,
                pexpect.TIMEOUT,
                pexpect.EOF,
            ], timeout=30)

        if index != 0:
            _LOG.info("Login Failure")
            self._child = None
            raise TemporaryFailure("Login Failure")

        _LOG.info("Login Successful")
        return self

    def disconnect(self):
        _LOG.info("Disconnecting")
        self._child.sendline("exit")
        index = self._child.expect([
                CLOSED,
                pexpect.EOF,
                pexpect.TIMEOUT,
            ], timeout = 15 )

        self._child.close()
        self._child = None

    def execute_text(self, text):
        #Consume previous text
        self._child.expect([PROMPT, pexpect.TIMEOUT], timeout=0)

        #Send lines
        for line in text.splitlines():
            self._child.sendline(line)

    def send_if_no_echo(self, text):
        self._child.waitnoecho(0)
        self._child.sendline(text)

