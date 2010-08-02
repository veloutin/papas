import pexpect, re
import socket
import logging

_LOG = logging.getLogger("protocols.telnet")

from ..protocol import ConsoleProtocol

LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
FAILURE = re.compile(r"failed", re.I)
CLOSED = re.compile(r"closed", re.I)
PROMPT = re.compile(r"(^|#)")

class Telnet(ConsoleProtocol):
    def __init__(self):
        self._child = None

    def connect(self, host, user, passwd):
        _LOG.info("Attempting to connect to %(user)s@%(host)s" % {"host":host, "user":user})
        try:
            target = socket.gethostbyname(host)
        except socket.gaierror as e:
            _LOG.info(str(e))
            raise ValueError("Invalid host: " + e.strerror)
        self._child = c = pexpect.spawn("telnet %s" % target)

        index = c.expect([
                LOGIN_PROMPT,
                pexpect.TIMEOUT,
                pexpect.EOF,
            ], timeout=30)

        if index == 0:
            c.sendline(user) #Make sure it is the right end of line CR/LF?
        else:
            _LOG.info("Unable to get prompt")
            c.terminate()
            self._child = None
            return None

        c.waitnoecho( 30 )
        c.sendline(passwd)

        index = c.expect([
                PROMPT,
                LOGIN_PROMPT,
                FAILURE,
                pexpect.TIMEOUT,
                pexpect.EOF,
            ], timeout=30)
        if index == 0:
            _LOG.info("Login Successful")
            return c
        else:
            _LOG.info("Login Failure")
            _LOG.debug(c.before)
            return None

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


