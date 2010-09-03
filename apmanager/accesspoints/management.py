# coding: utf-8

from django.conf import settings
from django.db.models.signals import post_syncdb
from apmanager.accesspoints import models

PROTOCOLS = (
    {
        "protocol":dict(
            modname = "lib6ko.protocol.ConsoleProtocol",
            mode = None,
        ),
        "children":(
            {
                "protocol":dict(
                    modname = "lib6ko.protocols.telnet.Telnet",
                    mode = "console",
                ),
            },
        ),
    },
    {
        "protocol":dict(
            modname = "lib6ko.protocol.SNMPProtocol",
            mode = None,
        ),
        "children":(
            {
                "protocol":dict(
                    modname = "lib6ko.protocols.snmp.SNMP2cProtocol",
                    mode = "snmp",
                ),
            },
        ),
    },
)

def create_protocol(proto, parent=None):
    protocol, created = models.Protocol.objects.get_or_create(parent=parent, **proto["protocol"])

    for parameter in proto.get("parameters", ()):
        pass

    for child in proto.get("children", ()):
        create_protocol(child, protocol)


SECTIONS = {
    "SNMP" : [
        dict(
            name =          "Community",
#            field_type =    "text",
            default_value = None,
#            builtin = True,
        ),
        dict(
            name =          "traps",
#            field_type =    "text",
            default_value = None,
        ),
    ],
    "Console" : [
        dict(
            name =          "Telnet::Username",
#            field_type =    "str",
            default_value = "root",
#            builtin =       True,
        ),
        dict(
            name =          "Telnet::Password",
#            field_type =    "pwd",
##            builtin =       True,
        ),
        dict(
            name =          "SSH::Username",
#            field_type =    "str",
            default_value = "root",
#            builtin =       True,
        ),
        dict(
            name =          "SSH::Password",
#            field_type =    "pwd",
##            builtin =       True,
        ),
    ],
    "Network" : [
    ],
    "Wireless" : [
    ],
    "Ethernet" : [
    ],
    "Logging" : [
    ],

}

def create_protocols(sender, **kwargs):
    created_models = kwargs.get("created_models", None)
    verbosity = kwargs.get("verbosity", None)
    interactive = kwargs.get("interactive")

    for proto in PROTOCOLS:
        create_protocol(proto, None)

def create_sections(sender, **kwargs):
    created_models = kwargs.get("created_models", None)
    verbosity = kwargs.get("verbosity", None)
    interactive = kwargs.get("interactive")
    
    for name, value in SECTIONS.items():
        section = models.Section.objects.get_or_create(
            name=name, )[0]

        for option in value:
            models.Parameter.objects.get_or_create(section=section, **option)

post_syncdb.connect(create_sections, sender=models)
post_syncdb.connect(create_protocols, sender=models)
