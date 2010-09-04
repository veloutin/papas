from lib6ko.protocol import Protocol

class ConsoleProtocol(Protocol):
    LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
    FAILURE = re.compile(r"failed", re.I)
    CLOSED = re.compile(r"closed", re.I)
    PROMPT = re.compile(r"(>|#)")
    ROOT_PROMPT = re.compile(r"#")

    """ Console Protocol """
    def __init__(self, parameters):
        super(ConsoleProtocol, self).__init__(parameters)
        self.child = None
        self.EXIT_CMD = self.require_param(
            _P.CONSOLE_EXIT,
            default="exit",
            )
    
    @property
    def connected(self):
        return self.child is not None

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected")
            return

        _LOG.info("Disconnecting")
        self.child.sendline(self.EXIT_CMD)
        index = self.child.expect([
                self.CLOSED,
                pexpect.EOF,
                pexpect.TIMEOUT,
            ], timeout = 15 )

        self.child.close()
        self.child = None
        
    def execute_text(self, text):
        #Consume previous text
        self.child.expect([self.PROMPT, pexpect.TIMEOUT], timeout=0)

        #Send lines
        for line in text.splitlines():
            self.child.sendline(line)

    def send_if_no_echo(self, text):
        self.child.waitnoecho(0)
        self.child.sendline(text)
