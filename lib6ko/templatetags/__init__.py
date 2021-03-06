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
import logging
_LOG = logging.getLogger("lib6ko.templatetags")


class CommandNodeBase( object ):
    """ This is the Base class for Template Nodes that are also
    and executable Command. """
    mode = None

    def __init__(self):
        self.backend = None
        self.render_hook = None

    def render(self, context):
        if hasattr(self, "do_render"):
            if self.render_hook:
                out = self.do_render(context)
                return self.render_hook(self, out)
            else:
                return self.do_render(context)
        else:
            return ""

    @contextlib.contextmanager
    def get_context(self, executer):
        _LOG.debug("Entering execution context for {0}".format(self))
        self.setUp()
        _LOG.debug("setUp done")
        try:
            yield self
        finally:
            _LOG.debug("Leaving execution context for {0}".format(self))
            self.tearDown()
            _LOG.debug("tearDown done")

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def execute_text(self, text):
        return self.backend.execute_text(text)

class ConsoleNodeBase( CommandNodeBase ):
    mode = "console"

class SNMPNodeBase( CommandNodeBase ):
    mode = "snmp"
