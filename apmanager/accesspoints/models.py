import logging
LOG = logging.getLogger('apmanger.accesspoints')
import commands

from django.db import models
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class AccessPoint ( models.Model ):
    """
        Represents an Access Point, with name, IP, MAC and description.
    """
    name = models.CharField( max_length=100,
        help_text=_(u"Host Name") )
    ipv4Address = models.IPAddressField( unique=True,
        help_text=_(u"IP address of the access point") )
    macAddress = models.CharField( max_length=17, unique=True,
        help_text=_(u"MAC address") )
    description = models.CharField( max_length=255,
        help_text=_(u"Short description / Location") )
    architecture = models.ForeignKey('Architecture')

    class Meta:
        ordering = ('name','ipv4Address',)

    def get_absolute_url(self):
        return reverse('apmanager.accesspoints.views.ap.view_ap', args=(self.id,))

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
        file(os.path.join(settings.AP_REFRESH_WATCH_DIR,str(self.id)),'w').close()
        
    def refresh_clients(self):
        LOG.debug("refreshing client list for %s", str(self))
        LOG.error("Not implemented yet!")

    def get_param_dict(self):
        res = {}

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
    
    def __unicode__(self):
        return _(u"Group: %s") % (self.name)
    __repr__ = __unicode__

    def get_absolute_url(self):
        return reverse('apmanager.accesspoints.views.apgroup.view_group', args=(self.id,))

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('Nom' + "&nbsp;".join(['' for i in range(10)]), ) 
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

#Import other models
from apmanager.accesspoints.architecture import *
from apmanager.accesspoints.apcommands import *
