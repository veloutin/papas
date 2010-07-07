from django.db import models
from django.core.urlresolvers import reverse

# Import Command 
import commands
from apmanager.settings import DEBUG
# Create your models here.


class AccessPoint ( models.Model ):
    """
        Represents an Access Point, with name, IP, MAC and description.
    """
    name = models.CharField( max_length=100,
        help_text=u"Host Name" )
    ipv4Address = models.IPAddressField( unique=True,
        help_text=u"IP address of the access point" )
    macAddress = models.CharField( max_length=17, unique=True,
        help_text=u"MAC address" )
    description = models.CharField( max_length=255,
        help_text=u"Short description / Location" )

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
        (ret, out) = commands.getstatusoutput(r'ssh -o BatchMode=yes -o StrictHostKeyChecking=no %(ip)s wl assoclist 2>/dev/null | cut -d" " -f 2' % {'ip':self.ipv4Address} )
        if DEBUG:
            print out, ret
        if ret == 0:
            #Attempt to get all IP for MAC in arp tables
            (ret, out2) = commands.getstatusoutput(r'ssh -o BatchMode=yes %(ip)s -o StrictHostKeyChecking=no cat /proc/net/arp 2>/dev/null | sed -e "1d;s/ \{1,\}/ /g" | cut -d" " -f 1,4' % {'ip':self.ipv4Address} )
            ipmap = {}
            if ret == 0:
                for line in out2.splitlines():
                    print line
                    ip,mac = line.split()
                    ipmap.update({mac:ip})
                
            #Delete all connected clients
            for c in self.apclient_set.all():
                c.delete()

            #Recreate all clients
            for mac in out.splitlines():
                print "client ip for mac %s is %s" % (mac, ipmap.get(mac))
                c = APClient()
                c.ipv4Address = ipmap.get(mac)
                c.macAddress = mac
                c.connected_to = self
                c.save()


class APGroup ( models.Model ):
    """
        Used to group Access Points into Groups
    """
    name = models.CharField ( max_length=100,
        help_text=u"Name of the Group", unique=True )
    accessPoints = models.ManyToManyField(AccessPoint,
        help_text=u"Access Points in this AP group")

    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return u"Groupe: %s" % (self.name)
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
        help_text=u"IP address of the client" )
    macAddress = models.CharField( max_length=17, 
        help_text=u"Client MAC address" )
    connected_to = models.ForeignKey( AccessPoint ) 
        

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('AP','IP','MAC')])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="/accesspoints/%d/">%s</a>' % (int(self.connected_to.id),self.connected_to.name),
            self.ipv4Address,self.macAddress)])



#Import other models
from apmanager.accesspoints.apcommands import *

