import contextlib
import logging
_LOG = logging.getLogger("lib6ko.templatetags")


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
        return self.protocol.execute_text(text)

    def get_full_output(self):
        return self.protocol.get_full_output()

class ConsoleNodeBase( CommandNodeBase ):
    mode = "console"

class SNMPNodeBase( CommandNodeBase ):
    mode = "snmp"
