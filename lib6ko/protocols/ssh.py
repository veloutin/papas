import pexpect, re
import pxssh
import socket
import logging
from gettext import gettext as _

_LOG = logging.getLogger("protocols.ssh")

from lib6ko import parameters as _P
from lib6ko.protocol import TemporaryFailure, PermanentFailure
from lib6ko.protocols.console import ConsoleProtocol


class SSH(ConsoleProtocol):
    def __init__(self, parameters):
        super(SSH, self).__init__(parameters)
        self._host = self.require("ap::ipv4Address")
        self._username = self.require_param(_P.SSH_USERNAME)
        if "'" in self._username:
            raise ValueError("Username contains invalid characters")
        self.priv_password = self._password = self.require_param(_P.SSH_PASSWORD)
        self._port = int(self.require_param(_P.SSH_PORT, default="22"))

    def connect(self):
        _LOG.info(_("Attempting to connect to {0._username}@{0._host}").format(self))
        try:
            target = socket.gethostbyname(self._host)
        except socket.gaierror as e:
            _LOG.error(str(e))
            raise PermanentFailure("Invalid host: " + e.strerror)

        # In theory, we could use
        # import pxssh
        # self.child = c = pxssh.pxssh()
        # pxssh.login(self._host, self._username, self._password)
        # c.prompt()
        #
        # What I observed is that due to improper handling of exceptions in 
        # pxssh, login() fails.
        _LOG.debug(_("Spawning child..."))
        self.child = c = pexpect.spawn(
            "ssh -l '{0._username}' -p {0._port} {options} {0._host}".format(
                self,
                options = "-o StrictHostKeyChecking=no",
                )
            )

        self.arch.console.send_password(self._password)

        if not self.arch.console.prompt(consume=False, timeout=15):
            _LOG.info("Login Failure")
            self.child = None
            raise TemporaryFailure("Login Failure")

        _LOG.info("Login Successful")
        return self


