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

import contextlib


class CommandNodeBase( object ):
    """ This is the Base class for Template Nodes that are also
    and executable Command. """
    mode = None

    def __init__(self):
        self.backend = None

    @property
    def protocol(self):
        # FIXME This assumes that get_protocol_chain will always return the
        # same chain. If this changes, bad things will happen
        return self.backend.get_protocol_chain(self.mode).protocol
            
    def render(self, context):
        if hasattr(self, "do_render"):
            if self.backend:
                out = self.do_render(context)
                return self.backend.register_output(self, out)
            else:
                return self.do_render(context)
        else:
            return ""

    @contextlib.contextmanager
    def get_context(self, executer):
        self.setUp()
        try:
            yield self
        finally:
            self.tearDown()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def execute_text(self, text):
        return self.protocol.execute_text(text)

    def get_full_output(self):
        return self.protocol.get_full_output()

class ConsoleNodeBase( CommandNodeBase ):
    mode = "console"

class SNMPNodeBase( CommandNodeBase ):
    mode = "snmp"
