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

from lib6ko import parameters as _P

from . import ConsoleNodeBase

class ConsoleNode(ConsoleNodeBase):
    def __init__(self):
        super(ConsoleNode, self).__init__()
        self._owns_connection = False

    def setUp(self):
        if not self.protocol.connected:
            self.protocol.connect()
            self._owns_connection = True

    def tearDown(self):
        if self._owns_connection:
            self.protocol.disconnect()

class RootConsoleNode(ConsoleNodeBase):
    def setUp(self):
        priv_cmd = self.protocol.require_param(_P.CONSOLE_PRIV_MODE)
        priv_password = self.protocol.require_param(
            _P.CONSOLE_PRIV_PASSWORD,
            default=self.protocol.priv_password,
            )
        if priv_cmd:
            self.protocol.execute_text(priv_cmd, expect_noecho=True)
            self.protocol.send_if_no_echo(priv_password)
            self.protocol.prompt()

    def tearDown(self):
        unpriv_cmd = self.protocol.require_param(_P.CONSOLE_PRIV_END)
        if unpriv_cmd:
            self.protocol.execute_text(unpriv_cmd)
            self.protocol.prompt()

class AllowOutputNode(ConsoleNodeBase):
    def setUp(self):
        self.protocol.allow_output = True

    def tearDown(self):
        self.protocol.allow_output = False

class SingleCommandNode(ConsoleNodeBase):
    def execute_text(self, text):
        return self.protocol.execute_command(text)
