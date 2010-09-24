from gettext import gettext as _
import logging
_LOG = logging.getLogger("lib6ko.architecture")

import re
import pexpect
from cStringIO import StringIO
from lib6ko.protocol import ScriptError

class Console(object):
    LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
    FAILURE = re.compile(r"failed", re.I)
    CLOSED = re.compile(r"closed", re.I)
    PROMPT = r".*?[>\$\#] ?"
    PROMPT_RE = re.compile(
        r"(?P<before>(?:.|\s)*)^(?P<prompt>{0})".format(PROMPT),
        re.MULTILINE,
        )

    def __init__(self, child=None):
        self._child = None
        self.child = child
        self.allow_output = False
        self._pending_prompt = ""
        self._sent_output = 0
    
    @property
    def child(self):
        return self._child

    @property
    def output(self):
        return self.child.logfile_read.getvalue()

    @property
    def unread_output(self):
        return self.child.logfile_read.getvalue()[self._sent_output:]

    def consume_output(self):
        out = self.unread_output
        self._sent_output += len(out)
        if len(out):
            _LOG.debug("Consuming output: {0}".format(out))
        return out

    def consume_output_re(self, expr):
        """ Attempt to match expr in pending output and consume it """
        out = self.unread_output
        match = re.match(expr, out)
        if match:
            self._sent_output += match.end()

        return match
        
    def restore_output(self, output):
        #TODO actually see if it matches?
        start = self._sent_output
        self._sent_output -= len(output)

    @child.setter
    def child(self, child):
        self._child = child
        if self._child is not None:
            #Make sure we do not allow buffering on this, as it screws up
            # everthing, but mostly us.
            # That's even worse #self._child.maxread = 1
            self._child.searchwindowsize = 2000
            self._child.logfile = StringIO()
            self._child.logfile_read = StringIO()
            self._child.logfile_send = StringIO()

    @child.deleter
    def child(self):
        self._child = None

    def clear_child_logs(self):
        """ Clear child log files """
        self._child.logfile.seek(0)
        self._child.logfile.truncate()
        self._child.logfile_read.seek(0)
        self._child.logfile_read.truncate()
        self._child.logfile_send.seek(0)
        self._child.logfile_send.truncate()

    def wait_for_prompt(self, consume_output=True, timeout=1):
        if self.child.expect([self.PROMPT_RE, pexpect.TIMEOUT], timeout=timeout) == 0:
            if consume_output:
                self.consume_output()
            return True
        else:
            return False
        

    def prompt(self, consume=True, timeout=1):
        """ Get the next prompt. If consume is false, we will remember that it
        was matched, until it is consumed. """
        _LOG.debug(_("Expecting a prompt... with timeout {0}").format(timeout))
        # Wait for a prompt to happen to increase the chances that we have one
        # ready in the output
        self.child.expect([self.PROMPT_RE, pexpect.TIMEOUT], timeout=timeout)

        #Check for more prompts if we missed some
        #while self.child.expect([self.PROMPT_RE, pexpect.TIMEOUT], timeout=0) == 0:
        #    pass

        #Now we get the output we still have not read
        output = self.consume_output()

        match = self.PROMPT_RE.match(output)
        if match:
            _LOG.debug("Got Prompt!")
            if not consume:
                self.restore_output(match.group("prompt"))
        else:
            _LOG.debug("Failed to get Prompt!")
            _LOG.debug("Output: {0}".format(repr(output)))

        return match is not None

    def send_password(self, password):
        if not self.child.getecho():
            _LOG.debug("Sending password...")
            self.child.sendline(password)
            return True
        else:
            _LOG.debug("Waiting for a password prompt...")
            if self.child.waitnoecho(timeout=1):
                _LOG.debug("Sending password...")
                self.child.sendline(password)
                return True

            _LOG.debug("Did not get a password prompt.")
            return False

    def execute_command(self, command, expect_noecho=False):
        _LOG.debug("="*40)
        _LOG.info(_("Executing {0}").format(repr(command[:80])))

        #Allow us to find new input/output only
        readlog = self.child.logfile_read
        oStart = len(readlog.getvalue())

        #Consume previous text
        self.prompt()
        if self.unread_output:
            _LOG.warn(_("There is still unread output: {0}").format(self.unread_output))

        _LOG.debug(_("Sending command..."))
        sentchars = self.child.sendline(command)

        # Look for the output we sent
        idx = self.child.expect([command, pexpect.TIMEOUT], timeout=0)
        if idx == 0:
            # We found what we sent, get our output
            idx = self.child.expect([self.PROMPT_RE, pexpect.TIMEOUT], timeout=0)
        else:
            _LOG.error("Unable to read sent command...")

        # Match what we just sent
        if self.consume_output_re(".*?" + command):
            # We got the command, get the output and prompt
            if expect_noecho:
                # We should expect a noecho
                self.child.waitnoecho(timeout=1)
                return self.consume_output()
            else:
                if self.unread_output:
                    _LOG.debug("Unread output: " + self.unread_output)
                # We should get another prompt, but not output
                self.wait_for_prompt(consume_output = False)
                match = self.PROMPT_RE.match(self.unread_output)
                if match:
                    #We found a match!
                    if not self.allow_output:
                        #Check if we got unexpected output
                        if len(match.group("before").strip()) > 0:
                            _LOG.error(_(
                                    u"Unexpected script output. {0}").format(
                                        match.group("before").strip(),
                                        ),
                                    )
                            raise ScriptError(_(u"Unexpected script output."), self.output)

                    prompt = match.group("prompt")
                    if prompt:
                        self.restore_output(prompt)
                else:
                    #No match for the prompt...??
                    _LOG.warn("Unable to find prompt!")
                    self.prompt()

        return readlog.getvalue()[oStart:]

        

class Architecture(object):
    def __init__(self, console_class=Console):
        self.console = console_class()

