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

from collections import defaultdict

from django.db import models
from django import forms
from django.forms import widgets
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template import Template

from lib6ko.protocol import Protocol as BaseProtocol
from lib6ko import templatetags as cmdtags

import re
TAG_LIBRARY = "commands"
TAG_EXTENDS_RE = re.compile("{% extends .*? %}", re.MULTILINE)

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
def _source_set_action(dict_, key, value):
    dict_[key] = value
def _source_inherit_action(dict_, key, value=None):
    pass
def _source_notset_action(dict_, key, value=None):
    del dict_[key]

SOURCE_TYPE_NOTSET = "notset"
SOURCE_TYPE_SET = "set"
SOURCE_TYPE_INHERIT = "inherit"
SOURCE_TYPE_ACTIONS = defaultdict(
    lambda : _source_set_action,
    {
        SOURCE_TYPE_NOTSET : _source_notset_action,
        SOURCE_TYPE_SET : _source_set_action,
        SOURCE_TYPE_INHERIT : _source_inherit_action,
    }
)

SUPPORT_TYPE_UNKNOWN = "unknown"
SUPPORT_TYPE_ERROR = "error"
SUPPORT_TYPE_UNVERIFIED = "unverified"
SUPPORT_TYPE_NO = "no"
SUPPORT_TYPE_OK = "ok"
SUPPORT_TYPES = (
    # Key                    # Verbose name
    (SUPPORT_TYPE_UNKNOWN,    _(u"Unknown")),
#    (SUPPORT_TYPE_UNVERIFIED, _(u"Not Verified")),
    (SUPPORT_TYPE_NO,         _(u"Not Supported")),
    (SUPPORT_TYPE_OK,         _(u"Supported")),
#    (SUPPORT_TYPE_ERROR,      _(u"Error occured")),
)

SUPPORT_TYPES_INFO = defaultdict(
    lambda: dict(
        usable = False,
    ),
    {
        SUPPORT_TYPE_UNKNOWN : dict(
            usable = True,
        ),
        SUPPORT_TYPE_UNVERIFIED : dict(
            usable = True,
        ),
        SUPPORT_TYPE_NO : dict(
            usable = False,
        ),
        SUPPORT_TYPE_OK : dict(
            usable = True,
        ),
    }
)

class Section (models.Model):
    name = models.CharField(
        unique = True,
        max_length = 255,
        verbose_name = _(u"Name"), )

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name', )
        verbose_name = _(u"Section")

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

    class Meta:
        ordering = ('name', )
        verbose_name = _(u"Parameter")

    def __unicode__(self):
        return _(u"Parameter: {0.scoped_name}").format(self)

    def get_admin_url(self):
        return reverse('admin:accesspoints_parameter_change', args=(self.name,))

    @property
    def scoped_name(self):
        # XXX Should we add the section or not?
        return self.name

class ParamTracer(object):
    tracer_key = "parameter_tracer"
    def __init__(self):
        self.params = {}

    def add_step(self, param, source, value, operation=None):
        self.params.setdefault(param, []).append(
            dict(
                source=source,
                value=value,
                operation=operation,
                )
            )

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

    class Meta:
        ordering = ('modname', )
        verbose_name = _(u"Protocol")

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

    def load_default_parameter_values(self):
        res = {}
        for pparam in self.protocolparameter_set.filter(
                parameter__default_value__isnull=False
            ):
            res[pparam.parameter.name] = pparam.parameter.default_value
        return res

class APProtocolSupport (models.Model):
    protocol = models.ForeignKey(Protocol,
        related_name="protocol_support",
        limit_choices_to=dict(
            mode__isnull=False,
            ),
        )
    ap = models.ForeignKey('AccessPoint',
        related_name="protocol_support",
        )
    priority = models.PositiveIntegerField(
        default = 10,
        help_text = _(u"The highest priority protocol is tried first for each mode. 0 = Highest priority."),
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
    
    @property
    def is_usable(self):
        return SUPPORT_TYPES_INFO[self.status]["usable"]

    class Meta:
        ordering = [
            'priority',
            ]
        verbose_name = _(u"Protocol Support")
        verbose_name_plural = _(u"Protocols Support")

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

    def get_admin_url(self):
        return reverse('admin:accesspoints_architecture_change', args=(self.id,))

    class Meta:
        ordering = ('name', )
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
        ordering = ('parameter', )
        unique_together = (
            ('parameter', 'protocol'),
        )
        verbose_name = _(u"Protocol Parameter")
        verbose_name_plural = _(u"Protocol Parameters")

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

    def __unicode__(self):
        return u"{0.parameter.name} [{0.value_type}: {0.value}]".format(self)

    class Meta:
        ordering = ('parameter', )
        unique_together = (
            ('parameter', 'arch'),
        )
        verbose_name = _(u"Architecture Parameter")
        verbose_name_plural = _(u"Architecture Parameters")

    def update_dict(self, d):
        return SOURCE_TYPE_ACTIONS[self.value_type](
            d,
            self.parameter.scoped_name,
            self.value,
            )

class APParameter (models.Model):
    parameter = models.ForeignKey(Parameter)
    ap = models.ForeignKey('AccessPoint')
    value = models.CharField(
        verbose_name = _(u"Value"),
        max_length = 255,
        null=True, blank=True, )

    def __unicode__(self):
        return u"{0.parameter.name} [{0.value}]".format(self)

    class Meta:
        ordering = ('parameter', )
        unique_together = (
            ('parameter', 'ap'),
        )
        verbose_name = _(u"AP Parameter")
        verbose_name_plural = _(u"AP Parameters")

    def update_dict(self, d):
        d[self.parameter.scoped_name] = self.value

class InitSection (models.Model):
    section = models.ForeignKey(Section)
    template = models.TextField(
        blank = True,
        null = False,
        verbose_name = _(u"Script Template"), )
    architecture = models.ForeignKey(Architecture)

    def compile_template(self):
        return compile_template(self.template)

    def __unicode__(self):
        return _(u"%(section)s for %(arch)s") % dict(
            section = self.section.name,
            arch = self.architecture,
            )

    class Meta:
        ordering = (
            'section__name',
            )
        unique_together = (
            ('section', 'architecture',),
        )
        verbose_name = _(u"Initialization Section")
        verbose_name_plural = _(u"Initialization Sections")

class ArchInitResult (models.Model):
    section = models.ForeignKey(InitSection)
    ap = models.ForeignKey('AccessPoint')
    status = models.IntegerField(
        null=True, blank=True,
        )
    output = models.TextField(
        null=True, blank=True,
        )
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _(u"Initialization Result")
        verbose_name_plural = _(u"Initialization Results")

    def __unicode__(self):
        return _(u"'{0.section}' initialization for '{0.ap}'").format(self)

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

    class Meta:
        ordering = ('name', )
        verbose_name = _(u"Command Definition")
        verbose_name_plural = _(u"Command Definitions")

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

    def get_implementation(self, ap):
        imp_list = self.commandimplementation_set.all()
        arch = ap.architecture
        while arch is not None:
            # Look for specific first
            for imp in imp_list:
                if imp.architecture == arch:
                    return imp
            # Then in the parent
            arch = arch.parent
        else:
            # Not found
            # FIXME error handling?
            return None

    def get_form(self):
        def form_save(form_self, cmdexec):
            from apmanager.accesspoints.models import UsedParameter
            for key, val in form_self.cleaned_data.items():
                u, c = UsedParameter.objects.get_or_create(name=key, command=cmdexec)
                u.value = val
                u.save()

        return type("CommandDefinitionParameterForm",
            (forms.Form, ), # bases
            dict(
                [ (p, forms.CharField()) for p in filter(
                    lambda s: len(s) > 0,
                    map(
                        unicode.strip, self.parameters.split(",")
                        ),
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

    def __unicode__(self):
        return u"{0.command} on {0.architecture}".format(self)

    def compile_template(self):
        return compile_template(self.template)
    class Meta:
        ordering = ('command', 'architecture', )
        unique_together = (
            ('command', 'architecture'),
            )
        verbose_name = _(u"Command Implementation")
        verbose_name_plural = _(u"Command Implementations")



def compile_template(raw_text):
    # Django adds \r\n when you edit text in the web interface, but we
    # only want to have \n, so replace them
    raw_text = raw_text.replace("\r\n", "\n")
    # Make sure we have the {% load commands %} in there
    load_tag = "{{% load {0} %}}".format(TAG_LIBRARY)
    if not load_tag in raw_text:
        #If a extends tag exists, we need to insert after it
        match = TAG_EXTENDS_RE.search(raw_text)
        if match:
            end = match.end()
            return Template(load_tag.join([
                raw_text[:end],
                raw_text[end:],
                ])
            )
        else:
            return Template(load_tag + raw_text)
        
    return Template(raw_text)
    
