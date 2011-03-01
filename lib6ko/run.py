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

import logging
from gettext import gettext as _
_LOG = logging.getLogger("lib6ko.run")

import re
import traceback
from operator import attrgetter
from itertools import imap, chain, izip
from cStringIO import StringIO
from copy import deepcopy

from lib6ko.templatetags import CommandNodeBase, ConsoleNodeBase, SNMPNodeBase
from .transport import (
    ConfigurationException,
    TransportException,
    ConnectionLost,
    )
from .architecture import Architecture
from .protocol import (
    ScriptError,
    ScopedDict,
    )
from .utils import log_sleep
from . import parameters as _P

def extract_top_level_nodes_command_nodes(iterable):
    nodes = []
    get_nodes = lambda n: n.get_nodes_by_type(CommandNodeBase)

    full_list_iter = chain(*imap(get_nodes, iterable))
    for node in full_list_iter:
        nodes.append(node)

        #For each node, discard subnodes
        for (sub, dis) in izip(
                get_nodes(node)[1:],
                full_list_iter,
            ):
            pass
        
    return nodes

class ProtocolChain(object):
    """ Protocol chain allows having more than one protocol for each mode.
    Each protocol will be tried until there is no more left.
    """
    def __init__(self, cls_list, parameters, architecture=None):
        # Test iterability of cls_list
        iter(cls_list)
        # Make sure there is a param dict in parameters
        self._parameters = parameters
        self._parameters.setdefault("param", {})

        self._arch = (architecture or Architecture)()
        self._protocol = None
        self._current_descriptor = None
        self._discared = []
        self._protocol_descriptors = cls_list
        self._parameters = parameters

    @property
    def protocol(self):
        if self._protocol:
            return self._protocol

        errorlog = []
        #Initialize the next one
        for p in self._protocol_descriptors[:]:
            try:
                #Copy the param dict
                config = deepcopy(self._parameters)
                params = config["param"]

                #Fetch the protocol default parameters
                default_params = p.load_default_parameter_values()

                #Update missing "param::paramname" in the dict
                for key, val in default_params.items():
                    if not key in params:
                        params[key] = val
                
                #Initialize the protocol
                self._protocol = p.get_class()(config, self._arch)
                self._current_descriptor = p
                return self._protocol
            except (ConfigurationException), e:
                msg = _("Missing configuration for transport {0}: {1}").format(p, e)
                _LOG.error(msg)
                errorlog.append(msg)
                self._protocol_descriptors.remove(p)
            except Exception, e:
                msg = _("Unhandled exception in transport {0} initialization: {1}").format(p, e)
                _LOG.error(msg)
                _LOG.debug(traceback.format_exc())
                errorlog.append(msg)
                self._protocol_descriptors.remove(p)
        else:
            #We didn't manage to get any protocol
            raise ScriptError(_("Unable to get a working protocol"), u"\n".join(errorlog))

    @protocol.deleter
    def protocol(self):
        if self._protocol:
            self._protocol_descriptors.remove(self._current_descriptor)
            self._protocol = None
            self._current_descriptor = None


class Executer (object):
    """ The Executer class is reponsible for taking a template and executing
    it on an access point. This will cause all Command Nodes (SNMP, Console)
    to execute themselves.

    The general idea behind how this work is based on these ideas:
    - Django templates know how to render themselves when given a context
    - Each template Node (If, Cycle, etc...) can have a different rendering
        mechanism, and we do not need/want to know what it is. A special
        consideration for If nodes is that we do not know if/which subnodes
        are actually to be rendered, as it depends on the context.
    - CommandNodes may be contained in any normal node, and may contain other
        normal nodes
    - We want the resulting script to be executed in the order that is is
        written, but most template nodes render their contents and then render
        themselves. So, if we want the order to be maintained, we need to 
        "execute" the resulting template, not each individual nodes

    In order to satisfy the limitations encountered here, we do this:
    - When a backend is attached, CommandNodes will render themselves, and
        then register their output in the Executer. They will then return
        an easily parsable tag instead of their output.
    - When we pre-render the template, we will get an executable script.
    - We then execute the script, using backends corresponding to the node
        types to execute command nodes
    """
    RE_TBLOCK = re.compile("^###PRERENDERED: (?P<id>\d+)###$", re.MULTILINE)
    TBLOCK = "\n###PRERENDERED: {0}###\n"

    def __init__(self, protocol_classes=()):
        self._rendered_templates = {}
        self._command_nodes = {}
        self.parameters = {}
        self.output = None
        self.status = None

        #Init the protocol class lists
        self._protocol_classes = {}
        for protocol in protocol_classes:
            modelist = self._protocol_classes.setdefault(protocol.mode, [])
            modelist.append(protocol)

    def _get_node_id(self, node):
        return str(hash(node))

    def get_output(self, node):
        node_id = self._get_node_id(node)
        return self._rendered_templates[node_id]

    def register_output(self, node, output):
        node_id = self._get_node_id(node)
        self._command_nodes[node_id] = node
        self._rendered_templates[node_id] = output
        return self.TBLOCK.format(node_id)

    def execute_template(self, template, ap, parameters={}, context_factory=lambda p:p):
        #Get protocols by mode
        self.parameters = params = ScopedDict(ap=ap, param=parameters)
        if not "ap" in parameters:
            parameters["ap"] = ap

        transports = {}
        for key, val in self._protocol_classes.items():
            transports[key] = ProtocolChain(val, params)

        arch = Architecture()
        engine = TextEngine(params, arch, transports)
        #Prerender the template
        text = self.prerender_template(template, context_factory(parameters), engine)
        self._execute_text(text)

        return engine.output

    def _partition_template_text(self, text):
        """ Split compiled template text into text and command nodes """
        start = 0
        for match in self.RE_TBLOCK.finditer(text):
            match_start, match_end = match.span()

            # Output the block before the match as text if non-empty
            if match_start - start > 0:
                yield text[start:match_start]

            # Output the node corresponding to the matched tag
            node_id = match.group("id")
            if node_id in self._command_nodes:
                yield self._command_nodes[node_id]
            else:
                _LOG.error(_("Unknown node id {0}").format(node_id))

            # Make sure we don't output the tag itself
            start = match_end

        # What's left is text
        if start < len(text):
            yield text[start:]

    def _execute_text(self, text, node=None):
        """ Recursive execution of templates """
        # The top level of this will not have a node, and must add the contents
        # of all nodes that will be executed. When there is a node, the return
        # value will be that node's output.
        res = u""
        #_LOG.debug("{0:=^70}".format(" Template text for {0:x}".format(id(node))))
        #_LOG.debug(text)
        #_LOG.debug("{0:=^70}".format(" end "))
        #Split the template in text and nodes
        for part in self._partition_template_text(text):
            if isinstance(part, CommandNodeBase):
                with part.get_context(self):
                    self._execute_text(self.get_output(part), node=part)
            else:
                if node:
                    node.execute_text(part)
                else:
                    part = part.strip()
                    if part:
                        _LOG.debug(_("Following text will not be executed: {0}").format(part))

    def prerender_template(self, template, context, engine=None):
        """ Pre-Render a Template and return the resulting text """
        #Get all CommandNodeBase instances in the template Tree
        nodes = chain(*(node.get_nodes_by_type(CommandNodeBase) for node in template) )

        #Attach self as a backend on all command nodes
        for node in nodes:
            node.render_hook = self.register_output
            node.backend = engine

        #Render the template, causing all concerned nodes
        return template.render(context)

class EState(object):
    UNKNOWN = ""
    PROMPT = "prompt"
    ROOT_PROMPT = "root_prompt"
    EMPTY = "empty"
    PW_PROMPT = "pass_prompt"
    OTHER = "other"


class InteractiveEngine(object):
    CMD_WAIT = "cmd_wait"
    _CMD_WAIT = 0.5
    _S = EState
    """ Interactive prompt engine """
    def __init__(self, interactive_transport, parameters, architecture):
        self._console = interactive_transport
        self.params = parameters or {}
        self.arch = architecture
        self.log = ""
        self._currentline = None

    @property
    def currentline(self):
        return self._currentline

    @property
    def state(self):
        if self._currentline is None:
            return EState.UNKNOWN
        elif self._currentline == "":
            return EState.EMPTY
        elif re.match(self.arch.shell.ROOT_PROMPT, self._currentline):
            return EState.ROOT_PROMPT
        elif re.match(self.arch.shell.PROMPT, self._currentline):
            return EState.PROMPT
        elif re.match(self.arch.shell.PASSWORD_PROMPT, self._currentline):
            return EState.PW_PROMPT
        else:
            return EState.OTHER


    def read(self):
        read = self._console.read()
        _LOG.debug("Read console output: '{0}'".format(repr(read)))
        out = ( self._currentline or "" ) + read
        line = None
        for fullline in out.splitlines(True):
            line = fullline.splitlines()[0]
            if line != fullline:
                self.log += line + "\n"

        self._currentline = line


    def wait_for_output(self, timeout=0):
        _LOG.debug("Waiting on any output for {0}s".format(timeout))
        lout = len(self.log)
        for none in log_sleep(timeout, _LOG):
            if len(self.log) != lout:
                return True
        else:
            return False

    def wait_for_state(self, states, timeout=0):
        if not isinstance(states, (list, tuple)):
            states = (states, )

        _LOG.debug("Waiting for states {0} with timeout {1}"
            .format(
                states,
                timeout,
            )   )

        self.read()
        if self.state in states:
            return True

        for none in log_sleep(timeout, _LOG):
            self.read()
            if self.state in states:
                return True
        else:
            return False

    def send_command(self, command, next_state=None):
        """
        Send a line to the transport, return everything until the next prompt.
        """
        if next_state is None:
            next_state = self.state

        out = self._currentline or ""
        start = len(self.log) + len(out)

        self._console.write(command)

        wait = self.params.get(self.CMD_WAIT, "param", self._CMD_WAIT)
        self.wait_for_output(wait)
        self.wait_for_state(next_state)
        
        return self.log[start:]
            

class TextEngine(object):
    def __init__(self, parameters, arch, transports=None):
        self.params = parameters
        self.arch = arch

        #Init the transport chains
        self.transports = transports or {}

        # Execution output
        self._active_transport = None
        self._engine = None
        self.output = ""
        self.allow_output = False

    @property
    def connected(self):
        return not self._active_transport is None

    @property
    def interactive(self):
        return not self._engine is None

    @property
    def engine(self):
        return self._engine

    @property
    def transport(self):
        return self._active_transport

    def connect(self, mode):
        if self._active_transport:
            return self._active_transport
        # FIXME Handle conflicting modes?

        if not mode in self.transports:
            _LOG.error("Mode {0} has no available transport.".format(mode))
            raise Exception("No available {0} transport.".format(mode))
    
        while self._active_transport is None:
            transport = self.transports[mode].protocol
            try:
                transport.connect()
            except TransportException, e:
                self.output += "Unable to connect to {0}: {1}\n".format(
                    transport,
                    e,
                    )
                del self.transports[mode].protocol
            else:
                self._active_transport = transport

        if self.params.get(_P.CONSOLE_FORCE_INTERACTIVE, "param", default=""):
            self.start_interactive()

    def disconnect(self):
        if self.interactive:
            self.end_interactive()
        self._active_transport.disconnect()

    def start_interactive(self):
        if not self.interactive:
            self._engine = InteractiveEngine(
                self._active_transport,
                self.params,
                self.arch,
                )

    def end_interactive(self):
        if self.interactive:
            try:
                self._engine.wait_for_state(
                    (EState.PROMPT, EState.ROOT_PROMPT),
                    5,
                    )
                cmd = self.params.get(_P.CONSOLE_EXIT,
                    prefix="param",
                    default="exit",
                    )
                self._engine.send_command(cmd + "\n")
            except ConnectionLost:
                _LOG.debug("Connection lost on exit.")
            self.output += self._engine.log
            self._engine = None

    def execute_command(self, command):
        if self.interactive:
            self._engine.wait_for_state(
                (EState.PROMPT, EState.ROOT_PROMPT),
                5,
                )
            out = self._engine.send_command(command)
            out = out.replace(command, "")
            if len(out) and not self.allow_output:
                raise ScriptError("Unexepected output",
                    "Output :\n==============\n{0}"
                    "Full Log:\n=============\n{1}"
                    .format(
                        out,
                        self._engine.log,
                        )
                    )
                
        else:
            out = self._active_transport.execute(command)
            self.output += "$ {0}{1}".format(command, out)
            if len(out) and not self.allow_output:
                raise ScriptError("Unexpected output", out)

    def execute_text(self, text):
        if self.interactive:
            for line in text.splitlines():
                self.execute_command(line + "\n")
        else:
            self.execute_command(text)
