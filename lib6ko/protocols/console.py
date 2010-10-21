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

import re
import logging
import pexpect
from cStringIO import StringIO

from lib6ko import parameters as _P
from lib6ko.protocol import Protocol
from lib6ko.architecture import Architecture

_LOG = logging.getLogger("lib6ko.protocols.console")

class ConsoleProtocol(Protocol):

    """ Console Protocol """
    def __init__(self, parameters):
        super(ConsoleProtocol, self).__init__(parameters)
        self.EXIT_CMD = self.require_param(
            _P.CONSOLE_EXIT,
            default="exit",
            )
        self.priv_password = None
        self._init_architecture()
    
    def _init_architecture(self):
        self.arch = Architecture()

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
    
    def prompt(self, timeout=1):
        self.arch.console.prompt(consume=True, timeout=timeout)

    def execute_command(self, text, expect_noecho=False):
        self.arch.console.execute_command(text, expect_noecho)
        return self.arch.console.consume_output()

    def execute_text(self, text, expect_noecho=False):
        return "".join((self.execute_command(line, expect_noecho) for line in text.splitlines()))

    def get_full_output(self):
        return self.arch.console.output

    def send_if_no_echo(self, text):
        self.arch.console.send_password(text)
        self.arch.console.prompt(consume=False)
