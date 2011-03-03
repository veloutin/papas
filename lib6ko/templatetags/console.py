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
import logging
_LOG = logging.getLogger("lib6ko.templatetags.console")

from . import ConsoleNodeBase

class ConsoleNode(ConsoleNodeBase):
    def __init__(self):
        super(ConsoleNode, self).__init__()
        self._owns_connection = False

    def setUp(self):
        if not self.backend.connected:
            self.backend.connect(self.mode)
            self._owns_connection = True

    def tearDown(self):
        if self._owns_connection and self.backend.connected:
            self.backend.disconnect()

class RootConsoleNode(ConsoleNodeBase):
    def __init__(self):
        super(RootConsoleNode, self).__init__()
        self._started_interactive = False
        self._noop = False

    def setUp(self):
        priv_cmd = self.backend.params.get(_P.CONSOLE_PRIV_MODE, prefix="param")
        if not priv_cmd:
            _LOG.debug("No priv command, NOOP")
            self._noop = True
        else:
            priv_password = self.backend.params.get(
                _P.CONSOLE_PRIV_PASSWORD,
                prefix="param",
                default=getattr(self.backend.transport, "priv_password", None),
                )
            
            if not self.backend.interactive:
                self.backend.start_interactive()
                self._started_interactive = True

            engine = self.backend.engine
            if engine.wait_for_state(engine._S.ROOT_PROMPT, 2):
                return

            engine.send_command(
                priv_cmd + "\n",
                next_state=engine._S.PW_PROMPT,
                )
            if not engine.wait_for_state(engine._S.PW_PROMPT, 5):
                # Check if we already got root, just in case
                if not engine.state == engine._S.ROOT_PROMPT:
                    raise Exception("Unable to get root.")
            engine.send_command(
                priv_password + "\n",
                next_state=engine._S.ROOT_PROMPT,
                )
            if not engine.wait_for_state(engine._S.ROOT_PROMPT, 5):
                raise Exception("Unable to get root prompt.")

    def tearDown(self):
        if self._noop or not self.backend.connected:
            return

        engine = self.backend.engine
        unpriv_cmd = self.backend.params.get(
            _P.CONSOLE_PRIV_END,
            prefix="param",
            default="")
        if unpriv_cmd:
            engine.send_command(
                unpriv_cmd + "\n",
                engine._S.PROMPT,
                )
            engine.wait_for_state( engine._S.PROMPT, 5)

        if self._started_interactive:
            self.backend.end_interactive()

class AllowOutputNode(ConsoleNodeBase):
    def __init__(self):
        self.oldval = False

    def setUp(self):
        self.oldval = self.backend.allow_output
        self.backend.allow_output = True

    def tearDown(self):
        self.backend.allow_output = self.oldval

class SingleCommandNode(ConsoleNodeBase):
    def execute_text(self, text):
        return self.backend.execute_command(text)

class ConnectionDropNode(ConsoleNodeBase):
    def get_context(self, executer=None):
        # executer useless in that context, keep to match interface
        return self

    def __enter__(self):
        return self

    def __exit__(self, extype, exvalue, traceback):
        from lib6ko.transport import ConnectionLost
        return isinstance(exvalue, ConnectionLost)

    def execute_text(self, text):
        return
