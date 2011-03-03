import logging
_LOG = logging.getLogger(__name__)

import subprocess
import socket
import fcntl
import re
import os

from lib6ko.transport import (
    BaseTransport,
    ConnectedTransport,
    InteractiveTransport,
    TransportException,
    ConnectionLost,
    )
from lib6ko.utils import log_sleep
from lib6ko import parameters as _P


class Telnet(BaseTransport,
    ConnectedTransport,
    InteractiveTransport,
    ):
    def __init__(self, parameters, architecture):
        super(Telnet, self).__init__(parameters, architecture)
        self._client = None
        self._port = 23
        self._pending_out = ""

        # CFG
        self._host = self.require("ap::ipv4Address")
        self._username = self.require_param(_P.TELNET_USERNAME)
        self.priv_password = self._password = self.require_param(_P.TELNET_PASSWORD)
        self._port = self.require_param(_P.TELNET_PORT, default=23)

    @property
    def connected(self):
        return not self._client is None

    def connect(self):
        if self.connected:
            _LOG.info("Already connected.")
            return

        try:
            hostname = socket.gethostbyname(self._host)
        except socket.gaierror as e:
            _LOG.error(str(e))
            raise TransportException("Invalid host: " + e.strerror)

        _LOG.info("Spawning telnet {0} {1}".format(hostname, self._port))
        client = subprocess.Popen(
            ["telnet", hostname, str(self._port)],
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            )

        _LOG.debug("Spawned.")
        #Make stdout non-blocking for reads
        fcntl.fcntl(
            client.stdout,
            fcntl.F_SETFL,
            fcntl.fcntl(client.stdout, fcntl.F_GETFL) | os.O_NONBLOCK,
            )

        self._client = client
        eoi = 0
        match = self._get_match(self.arch.shell.LOGIN_PROMPT, eoi, 30)
        if not match:
            _LOG.error("Unable to get username prompt.")
            self._client = None
            raise TransportException("Unable to get username prompt.")

        eoi += match.end()
        self.write_line(self._username)
        match = self._get_match(self.arch.shell.PASSWORD_PROMPT, eoi, 15)
        if not match:
            _LOG.error("Unable to get password prompt.")
            self._client = None
            raise TransportException("Unable to get password prompt.")

        self.write_line(self._password)
        eoi += match.end()
        match = self._get_match(
            (self.arch.shell.PROMPT, self.arch.shell.ROOT_PROMPT),
            eoi,
            15,
            )
        if not match:
            _LOG.error("Unable to get command prompt.")
            self._client = None
            raise TransportException("Unable to get command prompt.")

        _LOG.info("Login Successful.")

    def disconnect(self):
        ### FIXME Do it properly
        if not self.connected:
            _LOG.warn("Already Disconnected.")
            return

        _LOG.info("Disconnecting.")
        self._client.terminate()
        self._client = None


    def write(self, data):
        _LOG.debug("Sending data: {0}".format(data))
        try:
            self._client.stdin.write(data)
        except IOError, e:
            if e.errno == os.errno.EPIPE:
                #Broken pipe -> disconnected
                raise ConnectionLost()
            else:
                raise

    def _read(self):
        try:
            return self._client.stdout.read()
        except IOError, e:
            _LOG.debug("IOError: {0}".format(e))
            if e.errno == os.errno.EPIPE:
                #Broken pipe -> disconnected
                raise ConnectionLost()

            # Prevent the Temporarily Unavailable error
            if e.errno == os.errno.EWOULDBLOCK:
                return ""
            else:
                raise

    def read(self):
        out = self._pending_out + self._read()
        self._pending_out = ""
        return out


    def _read_ahead(self):
        read = self._read()
        _LOG.debug("New output: {0}".format(repr(read)))
        self._pending_out += read

    def _get_match(self, patterns, start=0, timeout=0):
        _LOG.debug("Current pending out: {0}".format(self._pending_out))
        if not isinstance(patterns, (list, tuple)):
            patterns = (patterns, )
        self._read_ahead()
        for pattern in patterns:
            match = re.search(pattern, self._pending_out[start:])
            if match:
                return match

        for step in log_sleep(timeout, _LOG):
            self._read_ahead()
            for pattern in patterns:
                match = re.search(pattern, self._pending_out[start:])
                if match:
                    return match

        return None
