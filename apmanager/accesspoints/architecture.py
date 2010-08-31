# coding: utf-8
"""
Architecture todo

 .---------------.       .-------------.
 | Architecture  |-------| Map         |
 +---------------+       '------+------'
 | -SNMP Map     |              |
 | -Console Map  |              |*
 | -Initial Conf |       .------+------.
 '---------------'       | Parameter   |
                         +-------------+
          .----------.   |  -key       |
          | Section  |---|  -value     |
          '----------'   '-------------'
"""

import logging
LOG = logging.getLogger('apmanger.accesspoints')
import commands

from django.db import models
from django import forms
from django.forms import widgets
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from lib6ko.protocol import Protocol as BaseProtocol
from lib6ko import templatetags as cmdtags


CONTROL_MODE_CONSOLE = cmdtags.ConsoleNodeBase.mode
CONTROL_MODE_SNMP = cmdtags.SNMPNodeBase.mode
CONTROL_MODES = (
    (CONTROL_MODE_CONSOLE , _(u"Console")),
    (CONTROL_MODE_SNMP    , _(u"SNMP")),
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

SUPPORT_TYPE_UNKNOWN = "unknown"
SUPPORT_TYPE_ERROR = "error"
SUPPORT_TYPE_UNVERIFIED = "unverified"
SUPPORT_TYPE_NO = "no"
SUPPORT_TYPE_OK = "ok"
SUPPORT_TYPES = (
    (SUPPORT_TYPE_UNKNOWN, _(u"Unknown")),
    (SUPPORT_TYPE_UNVERIFIED, _(u"Not Verified")),
    (SUPPORT_TYPE_NO, _(u"Not Supported")),
    (SUPPORT_TYPE_OK, _(u"Supported")),
    (SUPPORT_TYPE_ERROR, _(u"Error occured")),
)


class Section (models.Model):
    name = models.CharField(
        primary_key = True,
        unique = True,
        max_length = 255,
        verbose_name = _(u"Name"), )

    def __unicode__(self):
        return self.name

class Parameter (models.Model):
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

class Protocol (models.Model):
    modname = models.CharField(
        primary_key = True,
        max_length = 255,
        verbose_name = _(u"Name"),
        editable = False,
        )
    parent = models.ForeignKey('self',
        null = True,
        editable = False,
        )
    mode = models.CharField(
        verbose_name = _(u"Mode"),
        max_length = 255,
        blank = True, null = True,
        choices = CONTROL_MODES, )

    def __unicode__(self):
        return self.modname

    def get_class(self):
        try:
            mod, sep, cls = self.modname.rpartition(".")
            mod = __import__(mod, fromlist=[cls])
            return getattr(mod, cls)
        except ImportError, e:
            LOG.error("Unable to import Protocol %s :\n%s" % (self.modname, str(e)))
            LOG.debug("Downgrading to BaseProtocol")
            return BaseProtocol

class APProtocolSupport (models.Model):
    protocol = models.ForeignKey(Protocol,
        related_name="protocol_support",
        )
    ap = models.ForeignKey('AccessPoint',
        related_name="protocol_support",
        )
    priority = models.IntegerField(
        default = 0,
        help_text = _(u"The highest priority protocol is tried first for each mode"),
        )
    status = models.CharField(
        max_length=32,
        verbose_name = _(u"Status"),
        choices = SUPPORT_TYPES,
        default = "unknown",
        )
    message = models.TextField(
        null = True, blank = True,
        )

    class Meta:
        ordering = [
            'priority',
            ]

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


class ProtocolParameter (models.Model):
    protocol = models.ForeignKey(Protocol)
    parameter = models.ForeignKey(Parameter)
    optional = models.BooleanField(
        verbose_name = _(u"Optional"),
        default = False,
        )

    def __unicode__(self):
        return u"[%(proto)s] %(param)s%(opt)s" % dict(
            proto=self.protocol_id,
            param=self.parameter_id,
            opt=self.optional and "?" or "",
            )

    class Meta:
        unique_together = (
            ('parameter', 'protocol'),
        )

class ArchParameter (models.Model):
    parameter = models.ForeignKey(Parameter)
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
            ('parameter', 'arch'),
        )

class APParameter (models.Model):
    parameter = models.ForeignKey(Parameter)
    ap = models.ForeignKey('AccessPoint')
    value = models.CharField(
        verbose_name = _(u"Value"),
        max_length = 255,
        null=True, blank=True ,)

    class Meta:
        unique_together = (
            ('parameter', 'ap'),
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


class CommandDefinition (models.Model):
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

    def create_instance(self, target) :
        from apmanager.accesspoints.models import (
            AccessPoint,
            APGroup,
            )
        if isinstance( target, AccessPoint ):
            return self.__create_instance(accesspoint=target)
        elif isinstance( target, APGroup ):
            return self.__create_instance(group=target)
        else:
            raise NotImplementedError("command creation not implemented on objects of type %s" % type(target))

    def __create_instance ( self, **kwargs ):
        from apmanager.accesspoints.models import CommandExec
        cmd = CommandExec(command=self, **kwargs )
        cmd.save()
       
        #Created Elsewhere 
        #for param in self.commandparameter_set.iterator():
        #    p = UsedParameter(parameter=param, command=cmd)
        #    p.save()

        return cmd

    def getForm(self):
        def form_save(form_self, cmdexec):
            from apmanager.accesspoints.models import UsedParameter
            for key, val in form_self.cleaned_data.items():
                u, c = UsedParameter.objects.get_or_create(name=key, command=cmdexec)
                u.value = val
                u.save()

        return type("CommandDefinitionParameterForm",
            (forms.Form, ), # bases
            dict(
                [ (p, forms.CharField()) for p in map(
                    unicode.strip, self.parameters.split(",")
                    ) ],
                save = form_save,
            ), # attrs
        )

class CommandImplementation (models.Model):
    command = models.ForeignKey(CommandDefinition)
    architecture = models.ForeignKey(Architecture)
    template = models.TextField(
        verbose_name = _(u"Template"),
        )

    class Meta:
        unique_together = (
            ('command', 'architecture'),
            )
