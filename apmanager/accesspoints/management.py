# coding: utf-8

from django.db.models.signals import post_syncdb
from apmanager.accesspoints import models

SECTIONS = {
    "SNMP" : [
        dict(
            name =          "Communities",
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
    "Telnet" : [
        dict(
            name =          "Username",
#            field_type =    "str",
            default_value = "root",
#            builtin =       True,
        ),
        dict(
            name =          "Password",
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

def create_sections(sender, **kwargs):
    created_models = kwargs.get("created_models", None)
    verbosity = kwargs.get("verbosity", None)
    interactive = kwargs.get("interactive")
    
    for name, value in SECTIONS.items():
        section = models.Section.objects.get_or_create(
            name=name, )[0]

        for option in value:
            models.ArchOption.objects.get_or_create(section=section, **option)



post_syncdb.connect(create_sections, sender=models)
