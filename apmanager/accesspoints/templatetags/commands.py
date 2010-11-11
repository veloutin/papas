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

import os
import re
from functools import partial

from django import template


from lib6ko.templatetags import CommandNodeBase
from lib6ko.templatetags import SNMPNodeBase
from lib6ko.templatetags.console import (
    ConsoleNode,
    RootConsoleNode,
    AllowOutputNode,
    SingleCommandNode,
    ConnectionDropNode,
    )
from lib6ko.protocol import ScriptError

from apmanager.accesspoints.models import (
    SOURCE_TYPE_NOTSET,
    SOURCE_TYPE_INHERIT,
    SOURCE_TYPE,
    ParamTracer,
    )

from apmanager.accesspoints.models import Parameter

register = template.Library()

CONSOLE_TAG="console"
OUTPUT_TAG="output"
PRIVILEGED_TAG="root"
SINGLE_CMD_TAG="single"
MODE_TAG="mode"
SNMP_TAG="snmp"
PARAM_TAG="param"
ALLOW_DROP_TAG="allow_connection_lost"

######################################################################
# Parameter
######################################################################
class DjParameterNode(CommandNodeBase, template.Node):
    def __init__(self, parameter):
        CommandNodeBase.__init__(self)
        self.parameter = parameter

    def render(self, ctx):
        paramname = self.parameter.resolve(ctx)
        tracer = ctx.get(ParamTracer.tracer_key)
        if tracer:
            add_trace = partial(tracer.add_step, paramname)
        else:
            add_trace = lambda *a, **k: None

        ap = ctx.get("ap", None)
        if ap:
            # First we lookup the AP if possible
            param = ap.apparameter_set.filter(parameter__name=paramname)
            if len(param):
                add_trace(ap, param[0].value)
                return param[0].value
            else:
                add_trace(ap, None)

            # Then we look up the ap's architecture, and then it's parent, etc
            arch = ap.architecture
            while arch is not None:
                param = arch.options_set.filter(parameter__name=paramname)
                if len(param):
                    add_trace(
                        arch,
                        param[0].value,
                        SOURCE_TYPE[param[0].value_type]
                        )
                    if param[0].value_type == SOURCE_TYPE_NOTSET:
                        # Do not use the value if "NOTSET"
                        break
                    elif param[0].value_type == SOURCE_TYPE_INHERIT:
                        # Go see parent
                        continue
                    else:
                        # Otherwise return it
                        return param[0].value
                else:
                    add_trace(arch, None)
                arch = arch.parent

        # Then we look up in parameters globally
        param = Parameter.objects.filter(name=paramname, default_value__isnull=False)
        if param:
            add_trace(param, param[0].default_value)
            return param[0].default_value
        
        # Otherwise... not found!

        # If we are tracing, do not raise an error
        if tracer:
            return ""

        raise ScriptError(
            "Missing Parameter",
            "Parameter {0} ({1}) not found!".format(
                paramname, self.parameter),
            )

@register.tag(PARAM_TAG)
def do_paramnode(parser, token):
    args = token.split_contents()

    if len(args) != 2:
        raise template.TemplateSyntaxError(
            '{tag} requires one parameter'.format(tag=PARAM_TAG),
            )

    return DjParameterNode(parser.compile_filter(args[1]))


######################################################################
# Console
######################################################################
class DjConsoleNode(ConsoleNode, template.Node):
    def __init__(self, nodelist):
        ConsoleNode.__init__(self)
        self.nodelist = nodelist

    def do_render(self, ctx):
        return self.nodelist.render(ctx)

@register.tag(CONSOLE_TAG)
def do_console(parser, token):
    nodelist = parser.parse(('end' + CONSOLE_TAG,))
    if nodelist.get_nodes_by_type(SNMPNodeBase):
        raise template.TemplateSyntaxError(
            "{inner} cannot exist inside a {outer} tag".format(
                inner=SNMP_TAG,
                outer=CONSOLE_TAG,
                ),
            )
    parser.delete_first_token()
    return DjConsoleNode(nodelist)

######################################################################
# Allow Output Node
######################################################################
class DjOutputNode(AllowOutputNode, template.Node):
    def __init__(self, nodelist):
        AllowOutputNode.__init__(self)
        self.nodelist = nodelist

    def do_render(self, ctx):
        return self.nodelist.render(ctx)

@register.tag(OUTPUT_TAG)
def do_output(parser, token):
    nodelist = parser.parse(('end' + OUTPUT_TAG, ))
    parser.delete_first_token()
    for t in parser.tokens:
        if t.token_type == template.TOKEN_BLOCK and t.contents == "end" + CONSOLE_TAG:
            break
    else:
        raise template.TemplateSyntaxError("%s cannot exist outside of a %s tag" % (OUTPUT_TAG, CONSOLE_TAG))
    return DjOutputNode(nodelist)


######################################################################
# Root
######################################################################
class DjPrilegedNode(RootConsoleNode, template.Node):
    def __init__(self, nodelist):
        RootConsoleNode.__init__(self)
        self.nodelist = nodelist

    def do_render(self, ctx):
        return self.nodelist.render(ctx)

@register.tag(PRIVILEGED_TAG)
def do_root(parser, token):
    nodelist = parser.parse(('end' + PRIVILEGED_TAG, ))
    parser.delete_first_token()
    for t in parser.tokens:
        if t.token_type == template.TOKEN_BLOCK and t.contents == "end" + CONSOLE_TAG:
            break
    else:
        raise template.TemplateSyntaxError("%s cannot exist outside of a %s tag" % (PRIVILEGED_TAG, CONSOLE_TAG))
    return DjPrilegedNode(nodelist)

######################################################################
# SingleCommand
######################################################################

# RegExp to remove starting and trailing line returns
# TR_CRLF = re.compile("^(\r?\n)*|\r?\n$")
class DjSingleCommandNode(SingleCommandNode, template.Node):
    def __init__(self, nodelist):
        SingleCommandNode.__init__(self)
        self.nodelist = nodelist

    def do_render(self, ctx):
        out = self.nodelist.render(ctx)
        #Remove leading whitespace as it should be useless
        return out.lstrip()

@register.tag(SINGLE_CMD_TAG)
def do_singlecmd(parser, token):
    nodelist = parser.parse(('end' + SINGLE_CMD_TAG, ))
    parser.delete_first_token()
    for t in parser.tokens:
        if t.token_type == template.TOKEN_BLOCK and t.contents == "end" + CONSOLE_TAG:
            break
    else:
        raise template.TemplateSyntaxError("%s cannot exist outside of a %s tag" % (SINGLE_CMD_TAG, CONSOLE_TAG))
    return DjSingleCommandNode(nodelist)

######################################################################
# Allow Connection Lost
######################################################################

class DjDropConnectionNode(ConnectionDropNode, template.Node):
    def __init__(self, nodelist):
        ConnectionDropNode.__init__(self)
        self.nodelist = nodelist

    def do_render(self, ctx):
        return self.nodelist.render(ctx)

@register.tag(ALLOW_DROP_TAG)
def do_dropconnecttag(parser, token):
    nodelist = parser.parse(('end' + ALLOW_DROP_TAG, ))
    parser.delete_first_token()
    return DjDropConnectionNode(nodelist)
######################################################################
# SNMP
######################################################################
class DjSnmpNode(SNMPNodeBase, template.Node):
    def __init__(self, nodelist):
        SNMPNodeBase.__init__(self)
        self.nodelist = nodelist

    @classmethod
    def _check_lines(cls, text):
        for line in text.splitlines():
            line = line.strip()
            if len(line) == 0:
                continue
            if not len(line.split(" ")) in (1, 3):
                raise ValueError("line must contain 1 (get) or 3 (set) elements")
            yield line
                

    def do_render(self, ctx):
        return "\n".join(self._check_lines(self.nodelist.render(ctx)))

@register.tag(SNMP_TAG)
def do_snmp(parser, token):
    nodelist = parser.parse(('end' + SNMP_TAG, ))
    if nodelist.get_nodes_by_type(CommandNodeBase):
        raise template.TemplateSyntaxError("%s cannot exist inside a %s tag" % (CONSOLE_TAG, SNMP_TAG))
    parser.delete_first_token()
    return DjSnmpNode(nodelist)


