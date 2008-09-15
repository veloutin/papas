from django.db import models

# Import Command 
import commands
from apmanager.settings import DEBUG
# Create your models here.


class AccessPoint ( models.Model ):
    """
        Represents an Access Point, with name, IP, MAC and description.
    """
    name = models.CharField( maxlength=100, core=True,
        help_text="Host Name" )
    ipv4Address = models.IPAddressField( core=True, unique=True,
        help_text="IP address of the access point" )
    macAddress = models.CharField( maxlength=17, core=True, unique=True,
        help_text="MAC address" )
    description = models.CharField( maxlength=255,
        help_text="Short description / Location" )

    class Admin:
        list_display = ('name', 'ipv4Address', 'macAddress')

    class Meta:
        ordering = ('name','ipv4Address',)

    def __str__(self):
        return "AP: %s ( %s -- %s )" % (self.name, self.ipv4Address, self.macAddress)
    __repr__ = __str__

    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('Nom','IP','MAC','Description')])
    table_view_header = staticmethod(table_view_header)
    def table_view_footer():
        return None
    table_view_footer = staticmethod(table_view_footer)
    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="/accesspoints/%d/">%s</a>' % (int(self.id),self.name),
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
    name = models.CharField ( maxlength=100, core=True,
        help_text="Name of the Group", unique=True )
    accessPoints = models.ManyToManyField(AccessPoint, filter_interface=models.VERTICAL,
        help_text="Access Points in this AP group")
    class Admin:
        list_display = ('name',)

    class Meta:
        ordering = ('name',)
    
    def __str__(self):
        return "Group: %s" % (self.name)
    __repr__ = __str__

    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('Nom' + "&nbsp;".join(['' for i in range(10)]), ) 
            ])
    table_view_header = staticmethod(table_view_header)
    def table_view_footer():
        return None
    table_view_footer = staticmethod(table_view_footer)
    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in ('<a href="/groups/%d/">%s</a>' % (int(self.id),self.name),)])


class APClient ( models.Model ):
    """
        Client connected to an Access Point
    """
    ipv4Address = models.IPAddressField( core=False, null=True,
        help_text="IP address of the client" )
    macAddress = models.CharField( maxlength=17, core=True, 
        help_text="Client MAC address" )
    connected_to = models.ForeignKey( AccessPoint ) 
        

    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in ('AP','MAC','IP')])
    table_view_header = staticmethod(table_view_header)
    def table_view_footer():
        return None
    table_view_footer = staticmethod(table_view_footer)
    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="/accesspoints/%d/">%s</a>' % (int(self.connected_to.id),self.connected_to.name),
            self.ipv4Address,self.macAddress)])



#Import other models
from apmanager.accesspoints.apcommands import *

