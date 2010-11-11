# PAPAS Access Point Administration System
# Copyright (c) 2010 Revolution Linux inc. <info@revolutionlinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import logging
from gettext import gettext as _

_LOG = logging.getLogger("lib6ko.protocols.ssh")

from lib6ko import parameters as _P
from lib6ko.protocol import TemporaryFailure, PermanentFailure
from lib6ko.protocols.console import ConsoleProtocol

from lib6ko.architecture import Architecture
from lib6ko.architectures.paramiko_ssh import (
    ParamikoConsole,
    InteractiveParamikoConsole,
    )


class SSH(ConsoleProtocol):
    def __init__(self, parameters):
        super(SSH, self).__init__(parameters)
        self._host = self.require("ap::ipv4Address")
        self._username = self.require_param(_P.SSH_USERNAME)
        if "'" in self._username:
            raise ValueError("Username contains invalid characters")
        self.priv_password = self._password = self.require_param(_P.SSH_PASSWORD)
        self._port = int(self.require_param(_P.SSH_PORT, default="22"))

    def _init_architecture(self):
        if self.require_param(_P.CONSOLE_FORCE_INTERACTIVE, default=""):
            self.arch = Architecture(console_class=InteractiveParamikoConsole)
        else:
            self.arch = Architecture(console_class=ParamikoConsole)

    def connect(self):
        _LOG.info(_("Attempting to connect to {0._username}@{0._host}").format(self))
        try:
            target = socket.gethostbyname(self._host)
        except socket.gaierror as e:
            _LOG.error(str(e))
            raise PermanentFailure("Invalid host: " + e.strerror)

        _LOG.debug(_("Spawning child..."))
        self.child = ParamikoConsole.spawn_child(
            hostname = target,
            username = self._username,
            password = self._password,
            port = self._port,
            )

        _LOG.info("Login Successful")
        return self

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected")
            return

        _LOG.info("Disconnecting")
        self.child.close()
        self.child = None


