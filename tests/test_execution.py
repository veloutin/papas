import sys, os
import unittest

from django.template import Template, Context

from lib6ko.run import (
    Executer,
    ScriptError,
    )

from lib6ko.tests.mocks.protocols import (
    createProtocolDescriptor,
    FakeConsoleProtocol,
    )
from lib6ko.tests.mocks.models import MockAP

FakeConsole = createProtocolDescriptor("FakeConsole",
    base_protocol_class = FakeConsoleProtocol,
    )


def execute(executer, template, params={}, ap=MockAP(), context_factory=Context):
    return executer.execute_template(template, ap, params, context_factory)

class TestExecuter(unittest.TestCase):
    def test_execute_no_commands(self):
        e = Executer([])

        t = Template("")
        res = execute(e, t)
        self.assertEquals(res, "")

        t = Template("{% for i in a %}{{ i }}{% endfor %}")
        res = execute(e, t, {"a":"abcde"})
        self.assertEquals(res, "abcde")

    def test_execute_command_no_protocol(self):

        e = Executer([])

        t = Template("""{% load commands %}
        {% console %}do stuff{% endconsole %}""")
        self.assertRaises(
            ScriptError,
            execute,
                e, t,
            )

    def test_execute_command_no_echo(self):
        e = Executer([FakeConsole])
        t = Template("""{% load commands %}
        {% console %}do stuff{% endconsole %}""")
        res = execute(e, t)
        self.assertTrue("fake> do stuff" in res)

    def test_execute_command_echo(self):
        e = Executer([FakeConsole])
        t = Template("""{% load commands %}
        {% console %}echo do stuff{% endconsole %}""")
        self.assertRaises(
            ScriptError,
            execute,
                e, t,
            )

        t = Template("""{% load commands %}
        {% console %}{% output %}echo do stuff{% endoutput%}{% endconsole %}""")
        res = execute(e, t)
        self.assertTrue("fake> echo do stuff\r\necho do stuff" in res)

    def test_available_context(self):
        e = Executer([FakeConsole])
        t = Template("""{{ ap.ipv4Address }}""")
        res = execute(e, t)
        self.assertEquals(res, "127.0.0.1")

if __name__ == '__main__':
    unittest.main()

