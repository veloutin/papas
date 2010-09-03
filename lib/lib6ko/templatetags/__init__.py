import contextlib


class CommandNodeBase( object ):
    """ This is the Base class for Template Nodes that are also
    and executable Command. """
    mode = None

    def __init__(self):
        self._backend = None

    @property
    def backend(self):
        return self._backend

    @backend.setter
    def backend(self, value):
        self._backend = value

    @property
    def protocol(self):
        return self.backend.get_protocol_chain(self.mode).protocol
            
    def render(self, context):
        if self.backend:
            out = self.do_render(context)
            return self.backend.register_output(self, out)
        else:
            return self.do_render(context)

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
        self.protocol.execute_text(text)

class ConsoleNodeBase( CommandNodeBase ):
    mode = "console"

class SNMPNodeBase( CommandNodeBase ):
    mode = "snmp"