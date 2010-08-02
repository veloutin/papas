# coding: utf-8
"""
Architecture todo

 .---------------.       .-------------.
 | Architecture  |-------| Map         |
 +---------------+       '------+------'
 | -SNMP Map     |              |
 | -Console Map  |              |*
 | -Initial Conf |       .------+------.
 '---------------'       | Option      |
                         +-------------+
          .----------.   |  -key       |
          | Section  |---|  -value     |
          '----------'   '-------------'
"""

import logging
LOG = logging.getLogger('apmanger.accesspoints')
import commands

from django.db import models
from django.forms import widgets
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

CONTROL_MODES = (
    ("console" , _(u"Console")),
    ("snmp"    , _(u"SNMP")),
)

FIELD_TYPES = {
    "str"   : (_(u"String"), models.CharField),
    "int"   : (_(u"Integer"), models.IntegerField),
    "bool"  : (_(u"Boolean"), models.BooleanField),
    "text"  : (_(u"Text"), models.TextField),
    "pwd"   : (_(u"Password"), type("PasswordField", 
                    (models.CharField, ), {"widget": widgets.PasswordInput } )
                ),
    "ip"    : (_(u"IP Address"), models.IPAddressField),
}

SOURCE_TYPE = {
    "notset" : _(u"Not Set"),
    "inherit": _(u"Inherited"),
    "set"    : _(u"Set"),
}



class Section (models.Model):
    name = models.CharField(
        primary_key = True,
        unique = True,
        max_length = 255,
        verbose_name = _(u"Name"), )

    def __unicode__(self):
        return self.name

class ArchOption (models.Model):
    name = models.CharField(
        primary_key = True,
        max_length = 255,
        verbose_name = _(u"Name"), )
    section = models.ForeignKey(Section)
    ##Unused for now
    #field_type = models.CharField(
    #    verbose_name= _(u"Type"),
    #    max_length = 15,
    #    choices= [ (k, v[0]) for k, v in FIELD_TYPES.items()],)
    default_value = models.CharField(
        max_length = 255,
        verbose_name = _(u"Default Value"),
        null = True, blank=True, )

    def __unicode__(self):
        return self.section_id + u"." + self.name

class Architecture (models.Model):
    """
    Architectures define how to interact with an access point and provides
    essential information about the firmware and operation
    """
    parent = models.ForeignKey(u'self',
        null=True, blank=True,
        verbose_name=_(u"Parent"), )
    name = models.CharField(
        max_length = 255,
        verbose_name= _(u"Name"), )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u"Architecture")

class ArchOptionValue (models.Model):
    option = models.ForeignKey(ArchOption)
    arch = models.ForeignKey(Architecture, related_name="options_set")
    value_type = models.CharField(verbose_name = _(u"Source"), 
            max_length = 15,
            choices=SOURCE_TYPE.items()
        )
    value = models.CharField(
        verbose_name = _(u"Value"),
        max_length = 255,
        null=True, blank=True ,)

    class Meta:
        unique_together = (
            ('option', 'arch'),
        )

class InitSection (models.Model):
    section = models.ForeignKey(Section)
    template = models.TextField(
        blank = True,
        null = False,
        verbose_name = _(u"Script Template"), )
    architecture = models.ForeignKey(Architecture)
    mode = models.CharField(
        verbose_name = _(u"Mode"),
        max_length = 255,
        choices = CONTROL_MODES, )

    def __unicode__(self):
        return _(u"%(section)s for %(arch)s [%(mode)s]") % dict(
            section = self.section_id,
            arch = self.architecture,
            mode = self.mode, )
    class Meta:
        unique_together = (
            ('section', 'architecture',),
        )


class ConsoleCommand (models.Model):
    name = models.CharField(
        max_length = 100,
        verbose_name = _(u"Name"),
        )
    parameters = models.CharField(
        max_length = 250,
        verbose_name = _(u"Parameters"),
        blank = True,
        help_text = _(u"A comma separated list of parameters that the command takes"),
        )
    
    def __unicode__(self):
        return u"%(name)s(%(parameters)s)" % {"name":self.name, "parameters":self.parameters}

class ConsoleCommandImplementation (models.Model):
    command = models.ForeignKey(ConsoleCommand)
    architecture = models.ForeignKey(Architecture)
    template = models.TextField(
        verbose_name = _(u"Template"),
        )

    class Meta:
        unique_together = (
            ('command', 'architecture'),
            )
