import paramiko
import logging
_LOG = logging.getLogger("architectures.paramikpo")

from cStringIO import StringIO

from lib6ko.architecture import Console
from lib6ko.protocol import ScriptError

class ParamikoConsole(Console):
    def __init__(self, child=None):
        super(ParamikoConsole, self).__init__(child)
        self.log = StringIO()

    def _configure_child(self):
        pass

    def clear_child_logs(self):
        self.log.seek(0)
        self.log.truncate()

    @property
    def output(self):
        return self.log.getvalue()

    def wait_for_prompt(self, consume_output=True, timeout=1):
        return True

    def prompt(self, consume=True, timeout=1):
        return True

    def send_password(self, password):
        raise NotImplementedError("Use an interactive shell for passwords")

    def get_interactive(self):
        return InteractiveWrapper(self.child.invoke_shell(), self.log)

    def execute_command(self, command, expect_noecho=False):
        sin, sout, serr = self.child.exec_command(command)
        self.log.write("$ {0}\n".format(command))
        out = sout.read() + serr.read()
        self.log.write(out)
        
        if not self.allow_output and len(out.strip()) > 0:
            raise ScriptError("Unexpected script output", out)
        return out

    
    @classmethod
    def spawn_child(cls, hostname, username, password, port):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy(),
            )

        
        client.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            allow_agent=False,
            look_for_keys=False,
            )
        return client


class InteractiveWrapper(object):
    def __init__(self, channel, log):
        self.channel = channel
        self.log = log
    
    def send(self, data):
        self.log.write(data)
        self.channel.send(data)

    def send_line(self, line):
        self.log.write("$ ")
        self.send(line + "\n")
    
    def send_password(self, pw, lf="\n"):
        """ Send a password
        The password will be shown as stars in the log
        Parameters:
        - pw : password to send
        - lf : linefeed to send after or None
        """
        self.log.write("********")
        self.channel.send(pw)
        if lf:
            self.send(lf)

    def read(self):
        out = ""
        while self.channel.recv_ready():
            out += self.channel.recv(10000)

        self.log.write(out)
        return out

    def close(self):
        self.channel.close()
