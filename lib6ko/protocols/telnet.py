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

import pexpect, re
import socket
import logging
from gettext import gettext as _

_LOG = logging.getLogger("protocols.telnet")

from lib6ko import parameters as _P
from lib6ko.protocol import TemporaryFailure
from lib6ko.protocols.console import ConsoleProtocol


class Telnet(ConsoleProtocol):
    def __init__(self, parameters):
        super(Telnet, self).__init__(parameters)
        self._host = self.require("ap::ipv4Address")
        self._username = self.require_param(_P.TELNET_USERNAME)
        self.priv_password = self._password = self.require_param(_P.TELNET_PASSWORD)
        self._port = self.require_param(_P.TELNET_PORT, default=23)

    def connect(self):
        _LOG.info(_("Attempting to connect to {0._username}@{0._host}").format(self))
        try:
            target = socket.gethostbyname(self._host)
        except socket.gaierror as e:
            _LOG.error(str(e))
            raise PermanentFailure("Invalid host: " + e.strerror)

        self.child = c = pexpect.spawn("telnet %s %s" % (target, self._port))

        index = c.expect([
                self.arch.console.LOGIN_PROMPT,
                pexpect.TIMEOUT,
                pexpect.EOF,
            ], timeout=30)

        if index == 0:
            c.sendline(self._username) #Make sure it is the right end of line CR/LF?
        else:
            _LOG.info("Unable to get prompt")
            c.terminate()
            self.child = None
            raise TemporaryFailure("Unable to connect")

        self.arch.console.send_password(self._password)

        if not self.arch.console.prompt(consume=False, timeout=15):
            _LOG.info("Login Failure")
            self.child = None
            raise TemporaryFailure("Login Failure")

        _LOG.info("Login Successful")
        return self


