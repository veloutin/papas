import re
import time
import paramiko
import logging
_LOG = logging.getLogger("lib6ko.architectures.paramiko_ssh")

from gettext import gettext as _

from cStringIO import StringIO

from lib6ko.architecture import Console
from lib6ko.protocol import ScriptError, TemporaryFailure

_ErrChanClosed = _("""Connection closed unexpectedly.
Non-interactive mode might not be supported by access point.""")

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

    def get_interactive(self, echo=True):
        return InteractiveWrapper(
            self.child.invoke_shell(width=512), # Try to avoid backspace issues
            self.log,
            echo)

    def execute_command(self, command, expect_noecho=False):
        try:
            sin, sout, serr = self.child.exec_command(command)
        except (EOFError, AttributeError):
            # The channel can be closed unexpectedly, especially on Cisco
            # as it does not support non-interactive commands since it spawns
            # a local telnet shell when connected through ssh
            # This will either raise an EOFError or cause an attribute
            # lookup to fail in exec_command, raising an AttributeError
            raise TemporaryFailure(_ErrChanClosed)
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

        _LOG.info("Connecting to {0}@{1}:{2}".format(username, hostname, port))
        client.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            allow_agent=False,
            look_for_keys=False,
            )
        return client

class InteractiveParamikoConsole(ParamikoConsole):
    def __init__(self, child=None):
        super(InteractiveParamikoConsole, self).__init__(child)
        self._wrapper = None

    def _configure_child(self):
        self._wrapper = super(InteractiveParamikoConsole, self).get_interactive(
            echo=False,
            )

    def clear_child_logs(self):
        self.log.seek(0)
        self.log.truncate()

    @property
    def output(self):
        return self.log.getvalue()

    def _get_unread_prompt(self, consume=True):
        match = self.PROMPT_RE.match(self.unread_output)
        if match:
            if consume:
                #Consume the prompt
                self.consume_output(len(match.group()))
            else:
                #Otherwise, consume up to the prompt
                self.consume_output(len(match.group("before")))

            return True
        else:
            return False

    def wait_for_re(self, search, timeout=1):
        now = time.time()
        while (time.time() - now) < timeout:
            self._wrapper.read()
            match = re.match(search, self.unread_output)
            if match:
                return match
            time.sleep(0.1)
        else:
            # Timed out
            return None

    def wait_for_prompt(self, consume_output=True, timeout=1):
        if self._get_unread_prompt(consume_output):
            return True

        now = time.time()
        while (time.time() - now) < timeout:
            self._wrapper.read()
            if self._get_unread_prompt(consume_output):
                return True
            time.sleep(0.1)

        return True

    def prompt(self, consume=True, timeout=1):
        return self.wait_for_prompt(consume, timeout)

    def send_password(self, password):
        self._wrapper.send_password(password)

    def get_interactive(self):
        return self._wrapper

    def execute_command(self, command, expect_noecho=False):
        if not self.prompt():
            raise ScriptError("Unable to get prompt")

        self._wrapper.send_line(command)
        # Attempt to read sent command
        match = self.wait_for_re("^{0}".format(re.escape(command)))
        if match:
            self.consume_output(len(match.group()))
        else:
            _LOG.warning("Unable to read sent command")

        if expect_noecho:
            # Commands that expect a noecho will not output a prompt.
            # Since we cannot check for echo off, be kind and return
            return ""

        match = self.wait_for_re(self.PROMPT_RE)
        if match:
            out = match.group("before")

            if not self.allow_output and len(out.strip()) > 0:
                _LOG.error("Unexpected output:\n{0}\n{1}\n{0}".format(
                        "="*60,
                        self._report_error(command),
                        ),
                    )
                raise ScriptError(
                    "Unexpected script output",
                    self.output,
                    )
            return out
        else:
            _LOG.error("Command did not seem to return:\n{0}\n{1}\n{0}".format(
                    "="*60,
                    self._report_error(command),
                    ),
                )
            raise ScriptError(
                "Command did not seem to return.",
                self.output,
                )

    def _report_error(self, command):
        return "Command({3}):\n{0}\nOutput({4}):\n{1}\nFull({5}):\n{2}".format(
            repr(command),
            repr(self.unread_output),
            self.output,
            len(command),
            len(self.unread_output),
            len(self.output),
            )

class InteractiveWrapper(object):
    def __init__(self, channel, log, echo=True):
        self.channel = channel
        self.log = log
        self.echo = echo
    
    def send(self, data):
        if self.echo:
            self.log.write(data)
        self.channel.send(data)

    def send_line(self, line, lf="\n"):
        if self.echo:
            self.log.write("$ ")
        self.send(line + lf)
    
    def send_password(self, pw, lf="\n"):
        """ Send a password
        The password will be shown as stars in the log
        Parameters:
        - pw : password to send
        - lf : linefeed to send after or None
        """
        if self.echo:
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
