import logging
from gettext import gettext as _
LOG = logging.getLogger(__name__)

import re
from operator import attrgetter
from itertools import imap, chain, izip
from cStringIO import StringIO
from copy import deepcopy

from django.template import Context

from lib6ko.templatetags import CommandNodeBase, ConsoleNodeBase, SNMPNodeBase
from .protocol import (
    TemporaryFailure,
    PermanentFailure,
    MissingParametersException,
    ScopedDict,
    )

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
    def __init__(self, cls_list, parameters):
        self._protocol = None
        self._discared = []
        self._protos = cls_list
        self._parameters = parameters

    @property
    def protocol(self):
        if self._protocol:
            return self._protocol

        #Initialize the next one
        for p in self._protos[:]:
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
                self._protocol = p.get_class()(config)
                return self._protocol
            except TemporaryFailure:
                continue
            except (PermanentFailure, MissingParametersException):
                self._protos.remove(p)
                raise
        else:
            #We didn't manage to get any protocol
            if len(self._protos):
                raise TemporaryFailure(_("Unable to get a working protocol"))
            else:
                raise PermanentFailure(_("Unable to get a working protocol"))

    @protocol.deleter
    def protocol(self):
        if self._protocol:
            self._protos.remove(type(self._protocol))
            self._protocol = None


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

        #Init the protocol class lists
        self._protocol_classes = {}
        for protocol in protocol_classes:
            modelist = self._protocol_classes.setdefault(protocol.mode, [])
            modelist.append(protocol)

        self._protocol_chains = {}

    def get_protocol_chain(self, mode):
        return self._protocol_chains[mode]

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

    def execute_template(self, template, ap, parameters={}):
        #Get protocols by mode
        self.parameters = params = ScopedDict(ap=ap, param=parameters)

        #TODO: Use protocol support
        for key, val in self._protocol_classes.items():
            self._protocol_chains[key] = ProtocolChain(val, params)

        #for pro_sup in ap.protocol_support.all():
        #    modelist = cmd_modes.setdefault(pro_sup.protocol.mode, [])
        #    modelist.append(pro_sup.protocol)

        #Prerender the template
        text = self.prerender_template(template, Context(parameters))

        return self._execute_text(text)

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
                LOG.error(_("Unknown node id {0}").format(node_id))

            # Make sure we don't output the tag itself
            start = match_end

        # What's left is text
        if start < len(text):
            yield text[start:]

    def _execute_text(self, text, node=None):
        res = u""
        #Split the template in text and nodes
        for part in self._partition_template_text(text):
            if isinstance(part, CommandNodeBase):
                with part.get_context(self):
                    res += self._execute_text(self.get_output(part), node=part)
            else:
                if node:
                    res += node.execute_text(part)
                else:
                    res += "TEXTNODE" + part + "END"
        return res

    def prerender_template(self, template, context):
        """ Pre-Render a Template and return the resulting text """
        #Get all CommandNodeBase instances in the template Tree
        nodes = chain(*(node.get_nodes_by_type(CommandNodeBase) for node in template) )

        #Attach self as a backend on all command nodes
        for node in nodes:
            LOG.debug(_("Attaching backend to node %s"), str(node))
            node.backend = self

        #Render the template, causing all concerned nodes
        return template.render(context)
