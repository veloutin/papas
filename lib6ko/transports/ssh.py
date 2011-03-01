import socket
import paramiko

import logging
_LOG = logging.getLogger(__name__)

from lib6ko.transport import (
    BaseTransport,
    ConnectedTransport,
    InteractiveTransport,
    CommandTransport,
    TransportException,
    ConnectionLost,
    )
from lib6ko.utils import log_sleep
from lib6ko import parameters as _P


class SSH(BaseTransport,
    ConnectedTransport,
    InteractiveTransport,
    CommandTransport,
    ):
    def __init__(self, parameters, architecture):
        super(SSH, self).__init__(parameters, architecture)
        self._client = None
        self._shell = None

        self._host = self.require("ap::ipv4Address")
        self._username = self.require_param(_P.SSH_USERNAME)
        if "'" in self._username:
            raise ValueError("Username contains invalid characters")
        self.priv_password = self._password = self.require_param(_P.SSH_PASSWORD)
        self._port = int(self.require_param(_P.SSH_PORT, default="22"))

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

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy(),
            )

        _LOG.info("Connecting to {0}@{1}:{2}.".format(self._username, hostname, self._port))
        try:
            client.connect(
                hostname=hostname,
                username=self._username,
                password=self._password,
                port=self._port,
                allow_agent=False,
                look_for_keys=False,
                )
        except socket.error as e:
            _LOG.error(str(e))
            raise TransportException("Unable to connect: " + e.strerror)
        except paramiko.SSHException as e:
            _LOG.error(str(e))
            raise TransportException("Unable to connect: " + str(e))

        _LOG.info("Login Successful.")
        self._client = client

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected.")
            return

        _LOG.info("Disconnecting.")
        self._client.close()
        self._client = None


    @property
    def shell(self):
        if not self.connected:
            raise TransportException("Not connected.")

        closed = False
        if not self._shell is None:
            if self._shell.closed:
                closed = True
                _LOG.warn("Shell was closed, opening a new.")
            else:
                return self._shell

        try:
            self._shell = self._client.invoke_shell(width=512)
        except (EOFError, AttributeError) as e:
            if closed:
                raise ConnectionLost("Connection was lost")
            raise TransportException("Unable to invoke shell: {0}".format(e))
        return self._shell

    def write(self, data):
        shell = self.shell
        target = len(data)
        sent = 0
        while sent < target:
            for dlay in log_sleep(15, _LOG):
                if shell.send_ready():
                    break
                else:
                    _LOG.debug("Channel not ready to send data")
            else:
                if not shell.send_ready():
                    raise TransportException("Unable to send data.")


            bsent = shell.send(data[sent:])
            if bsent == 0:
                raise TransportException("Channel closed while sending data.")
            sent += bsent
            _LOG.debug("Sent {0} bytes. Total: {1} of {2}".format(
                bsent,
                sent,
                target))

    def read(self):
        shell = self.shell
        out = ""
        while shell.recv_ready():
            out += shell.recv(10000)

        return out

    def execute(self, command):
        if not self.connected:
            raise TransportException("Not connected.")
        try:
            sin, sout, serr = self._client.exec_command(command)
        except (EOFError, AttributeError):
            # The channel can be closed unexpectedly, especially on Cisco
            # as it does not support non-interactive commands since it spawns
            # a local telnet shell when connected through ssh
            # This will either raise an EOFError or cause an attribute
            # lookup to fail in exec_command, raising an AttributeError
            raise TransportException(
                "Connection closed unexpectedly. Remote host might be "
                "forcing a shell if this happens all the time."
                )
        return sout.read() + serr.read()
