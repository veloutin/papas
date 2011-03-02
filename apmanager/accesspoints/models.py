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
LOG = logging.getLogger('apmanager.accesspoints')

from django.db import models
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _u
from django.template import Context, TemplateSyntaxError

from apmanager.accesspoints.architecture import *

class AccessPoint ( models.Model ):
    """
        Represents an Access Point, with name, IP, MAC and description.
    """
    name = models.CharField( max_length=100,
        verbose_name = _(u"Name"),
        help_text=_(u"Host Name") )
    ipv4Address = models.IPAddressField( unique=True,
        verbose_name = _(u"IPv4 Address"),
        help_text=_(u"IP address of the access point") )
    macAddress = models.CharField( max_length=17, null=True, blank=True,
        verbose_name=_(u"MAC address") )
    description = models.CharField( max_length=255,
        help_text=_(u"Short description / Location") )
    architecture = models.ForeignKey('Architecture')

    class Meta:
        ordering = ('name','ipv4Address',)
        verbose_name = _("Access Point")
        verbose_name_plural = _("Access Points")

    def get_absolute_url(self):
        return reverse('apmanager.accesspoints.views.ap.view_ap', args=(self.id,))

    def get_admin_url(self):
        return reverse('admin:accesspoints_accesspoint_change', args=(self.id,))

    def __repr__(self):
        return u"AP: %s ( %s -- %s )" % (self.name, self.ipv4Address, self.macAddress)

    def __unicode__(self):
        return u"AP: %s" % (self.name)

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('Nom','IP','MAC','Description')])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="%s">%s</a>' % (self.get_absolute_url(), self.name),
            self.ipv4Address,self.macAddress,self.description)])

    def schedule_refresh(self):
        # Use the daemon if allowed by settings for asynchronous execution
        if settings.USE_DAEMON:
            file(os.path.join(settings.AP_REFRESH_WATCH_DIR,str(self.id)),'w').close()
        else:
            self.refresh_clients()
        
    def refresh_clients(self):
        LOG.debug("refreshing client list for %s", str(self))
        LOG.error("Not implemented yet!")

    def schedule_init(self):
        #Delete old results, simpler that way
        self.archinitresult_set.all().delete()
        # TODO Add a way to tell that it's still running
        if settings.USE_DAEMON:
            file(os.path.join(settings.AP_INIT_WATCH_DIR, str(self.id)), 'w').close()
        else:
            self.run_init()

    def run_init(self):
        from lib6ko.run import Executer
        from lib6ko.protocol import ScriptError
        from lib6ko.transport import TransportException

        #Make params dict
        params = self.get_param_dict()

        # Use the supported protocols
        protocols = self.protocol_support.all()

        # If there are no defined protocols, create them
        if len(protocols) == 0:
            for protocol in Protocol.objects.filter(mode__isnull=False):
                ap_pro_sup = APProtocolSupport.objects.create(
                    ap = self,
                    protocol = protocol,
                )

            protocols = self.protocol_support.all()

        executer = Executer(
            protocol_classes=[ p.protocol for p in protocols if p.is_usable ],
            )

        # Go through all init sections
        # Run sections ordered by section name
        for init_section in self.architecture.initsection_set.order_by('section__name'):
            try:
                apinit = self.archinitresult_set.get(section=init_section)
                apinit.status = -1
                apinit.output = _u(u"Initialization has not finished")
                apinit.save()
            except ArchInitResult.DoesNotExist:
                apinit = self.archinitresult_set.create(
                    section=init_section,
                    status=-1,
                    output=_u(u"Initialization has not finished"),
                    )

            # Execute the section
            try:
                apinit.output = executer.execute_template(
                    init_section.compile_template(),
                    self,
                    params,
                    context_factory=Context,
                    )
                apinit.status = 0
            except TemplateSyntaxError as e:
                # TemplateSyntaxError wraps the inner exception as provided
                # in the __exit__ of contextlib, see
                #http://docs.python.org/reference/datamodel.html#object.__exit__
                exc_type, exc_value, trace_obj = e.exc_info
                if exc_type is ScriptError:
                    apinit.output = exc_value.traceback
                    apinit.status = -1
                else:
                    apinit.output = traceback.format_exc()
                    apinit.status = -1
            except ScriptError as e:
                apinit.output = "{0}\n{0.traceback}".format(e)
                apinit.status = -1
            except TransportException as e:
                apinit.output = str(e)
                apinit.status = -1
            except Exception as e:
                apinit.output = traceback.format_exc()
                apinit.status = -1

            apinit.save()
        return

    def get_param_dict(self):
        res = {}

        #Get default values
        for param in Parameter.objects.filter(default_value__isnull=False):
            res[param.name] = param.default_value

        #Get params from architecture, and parent architecture
        arch = self.architecture
        arch_list = []
        while arch is not None:
            arch_list.append(arch)
            arch = arch.parent

        #Update parameters by starting from the arch hierarchy's top
        for arch in reversed(arch_list):
            for option in arch.options_set.all():
                option.update_dict(res)

        #Go through the AP's parameters
        for param in self.apparameter_set.all():
            param.update_dict(res)

        return res

    def get_full_param_information(self):
        """ Construct a dictionary containing all parameters and their value
        as obtained in get_param_dict().

        Each entry has the following structure
        {
            "parameter" : <Parameter object>,
            "trace" : [
                {
                    "source" : <Source Object>,
                    "value"  : <Parameter value>,
                    "action" : <Usage of value>,
                },
                ...
            ]
        }

        where "trace" will contain all the objects that were queried for
        the parameter value, according to the Parameter Resolution Order
        """
        res = {}

        # Default parameters
        for param in Parameter.objects.all():
            if param.default_value is None:
                action=_(u"No default value")
            else:
                action=_(u"Default value")

            res[param.name] = dict(
                parameter=param,
                trace=[
                    dict(
                        value=param.default_value,
                        action=action,
                        source=param,
                    )
                    ],
                value=param.default_value,
                )

        # Go through all parent architectures
        arch = self.architecture
        arch_list = []
        while arch is not None:
            arch_list.append(arch)
            arch = arch.parent

        #Update parameters by starting from the arch hierarchy's top
        for arch in reversed(arch_list):
            for opt in arch.options_set.select_related("parameter"):
                param = opt.parameter

                # Add the trace
                res[param.name]["trace"].insert(0, dict(
                    value=opt.value,
                    action=SOURCE_TYPE.get(opt.value_type, _("Unknown")),
                    source=arch,
                    )
                )

                # Update the value
                update_func = SOURCE_TYPE_ACTIONS.get(opt.value_type, lambda d, k, v: None)
                update_func(res[param.name], "value", opt.value)

        # Update the parameters with those on the AP
        for ap_param in self.apparameter_set.select_related("parameter"):
            param = ap_param.parameter

            res[param.name]["trace"].insert(0, dict(
                value=ap_param.value,
                action=_("Set"),
                source=self,
                )
            )
            res[param.name]["value"] = ap_param.value

        return res

class APGroup ( models.Model ):
    """
        Used to group Access Points into Groups
    """
    name = models.CharField ( max_length=100,
        help_text=_(u"Name of the Group"), unique=True )
    accessPoints = models.ManyToManyField(AccessPoint,
        help_text=_(u"Access Points in this AP group"))

    class Meta:
        ordering = ('name',)
        verbose_name = _("AP Group")
        verbose_name_plural = _("AP Groups")
    
    def __unicode__(self):
        return _u(u"Group: %s") % (self.name)
    __repr__ = __unicode__

    def get_absolute_url(self):
        return reverse('apmanager.accesspoints.views.apgroup.view_group', args=(self.id,))

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in (_u(u'Name') + "&nbsp;".join(['' for i in range(10)]), ) 
            ])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in ('<a href="%s">%s</a>' % (self.get_absolute_url(),self.name),)])

class APClient ( models.Model ):
    """
        Client connected to an Access Point
    """
    ipv4Address = models.IPAddressField( null=True,
        help_text=_(u"IP address of the client") )
    macAddress = models.CharField( max_length=17, 
        help_text=_(u"Client MAC address") )
    connected_to = models.ForeignKey( AccessPoint ) 
        

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('AP','IP','MAC')])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="%s">%s</a>' % (self.connected_to.get_absolute_url(),self.connected_to.name),
            self.ipv4Address,self.macAddress)])

class CommandTarget (object) :
    """ CommandTarget is used to wrap AccessPoint and APGroup into a common
    target for commands. Even though it accepts both, it will only use the
    AccessPoint if given an AccessPoint and an APGroup.
    """
    def __init__(self, ap=None, group=None):
        if ap:
            if isinstance(ap, AccessPoint):
                self._ap = ap
            else:
                self._ap = get_object_or_404(AccessPoint, pk=ap)
        else:
            self._ap = None

        if group:
            if isinstance(group, APGroup):
                self._group = group
            else:
                self._group = get_object_or_404(APGroup, pk=group)
        else:
            self._group = None

    @classmethod
    def fromQueryDict(cls, querydict, ap_id = "ap_id", group_id="group_id"):
        return cls(querydict.get(ap_id, None), querydict.get(group_id, None))

    @property
    def targets(self):
        if self._ap:
            return [self._ap]
        elif self._group:
            return self._group.accessPoints.all()
        else:
            return []

    @property
    def target(self):
        return self.ap or self.group

    def __nonzero__(self):
        """ Truth testing """
        return self._ap is not None or self._group is not None

    @property
    def ap(self):
        return self._ap

    @property
    def ap_id(self):
        return self.ap.id

    @property
    def group(self):
        return self._group

    @property
    def group_id(self):
        return self.group.id

    def __unicode__(self):
        return unicode(self.target)

#Import other models
from apmanager.accesspoints.apcommands import *
