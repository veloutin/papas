import os
from django import template

from lib6ko.templatetags import CommandNodeBase
from lib6ko.templatetags import SNMPNodeBase
from lib6ko.templatetags.console import ConsoleNode, RootConsoleNode

register = template.Library()

CONSOLE_TAG="console"
PRIVILEGED_TAG="root"
MODE_TAG="mode"
SNMP_TAG="snmp"
PARAM_TAG="param"

######################################################################
# Parameter
######################################################################
class ParameterNode(CommandNodeBase, template.Node):
    def __init__(self, parameter):
        self.parameter = parameter

    def render(self, ctx):
        return self.parameter.resolve(ctx)

@register.tag(PARAM_TAG)
def do_paramnode(parser, token):
    args = token.split_contents()

    if len(args) != 2:
        raise template.TemplateSyntaxError(
            '{tag} requires one parameter'.format(tag=PARAM_TAG),
            )

    return ParameterNode(parser.compile_filter(args[1]))


######################################################################
# Console
######################################################################
class ConsoleNode(ConsoleNode, template.Node):
    def __init__(self, nodelist):
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
    return ConsoleNode(nodelist)


######################################################################
# Root
######################################################################
class PrilegedNode(RootConsoleNode, template.Node):
    def __init__(self, nodelist):
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
    return PrilegedNode(nodelist)


######################################################################
# SNMP
######################################################################
class SnmpNode(SNMPNodeBase, template.Node):
    def __init__(self, nodelist):
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
    return SnmpNode(nodelist)


