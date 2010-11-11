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

import os, sys
import pexpect
from lib6ko.protocol import (
    Protocol,
    TemporaryFailure,
    )

from lib6ko.protocols.console import ConsoleProtocol


def createProtocolDescriptor(
        name,
        params={},
        failure=None,
        base_protocol_class=Protocol,
    ):
    """
    Protocol Descriptor Factory

    Returns classes that mimics the behavior of the
    apmanager.accesspoints.architecture.Protocol and provides:
     - load_default_parameter_values()
     - get_class()
    
    Parameters:
     - name : class name
     - params : dictionary of required parameters, where the key is the name
           and the value is the default_value
     - failure : allows forcing the protocol to launch an exception on init.
           If provided and not None, the provided value will be raised.  
    """

    class MockProtocol(base_protocol_class):
        def __init__(self, parameters):
            if failure:
                raise failure
            super(MockProtocol, self).__init__(parameters)
            for key, val in params.items():
                self.require_param(key, val)

    class _WrapperBase(object):
        def load_default_parameter_values(self):
            return dict(
                filter(
                    lambda s: s[1] is not None,
                    params.items(),
                    )
                )

        def get_class(self):
            return MockProtocol

        @property
        def mode(self):
            return MockProtocol.mode

    return type(
        #Class name
        name,
        #Bases
        (_WrapperBase, ),
        #Attributes
        {},
        )()


class FakeConsoleProtocol(ConsoleProtocol):
    mode = "console"

    def __init__(self, parameters):
        super(FakeConsoleProtocol, self).__init__(parameters)

    def connect(self):
        #Get the fake console module
        from lib6ko.tests.mocks import interactive_console
        target = os.path.abspath(interactive_console.__file__)
        self.child = c = pexpect.spawn("{0} {1}".format(
            sys.executable,
            target,
            ))

        #We use expect even though we know what happens, so that
        # a change in the expect libs can break this test
        index = c.expect([
                interactive_console.USERNAME,
                pexpect.TIMEOUT,
            ], timeout = 5)
        if index == 0:
            c.sendline("fakeuser")

        self.arch.console.send_password("fakeuser")

        if not self.arch.console.prompt(consume=False, timeout=5):
            raise TemporaryFailure("Login Failure")

        return self
