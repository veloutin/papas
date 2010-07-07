from django.db import models
from django.core.urlresolvers import reverse

from apmanager.accesspoints.models import AccessPoint, APGroup
from datetime import datetime
from apmanager import settings
from tempfile import mkstemp
import commands
import os,sys

def sleep_and_exit( exit=0, len='5s' ):
    os.system('sleep '+ len)
    return HttpResponseNotModified()
    sys.exit(exit)

class Command ( models.Model ):
    """
        Command to execute on an Access Point.
    """
    name = models.CharField( max_length=255,
        help_text=u"Display Name", unique=True )
    script = models.FileField ( upload_to=settings.UPLOAD_ROOT, blank=True )
    script_text = models.TextField( blank=True)

    def save(self):
        if self.script_text:
           self.script = ""
        models.Model.save(self)

   
    def __unicode__(self):
        return u"Script: %s" % self.name

    def __repr__(self):
        return u"Script: %s [%s]" % (self.name, self.script or self.script_text[0:30])

    def has_params(self):
        return self.commandparameter_set.count() > 0

    def create_instance(self,target) :
        if isinstance( target, AccessPoint ):
            return self.__create_instance(accesspoint=target)
        elif isinstance( target, APGroup ):
            return self.__create_instance(group=target)
        else:
            raise NotImplementedError("command creation not implemented on objects of type %s" % type(target))

    def __create_instance ( self, **kwargs ):
        cmd = CommandExec(command=self, **kwargs )
        cmd.save()
       
        #Created Elsewhere 
        #for param in self.commandparameter_set.iterator():
        #    p = UsedParameter(parameter=param, command=cmd)
        #    p.save()

        return cmd

from django import forms
class CommandParameter ( models.Model ):
    ALLOWED_TYPES = (
        (int,'Integer',forms.IntegerField),
        (str,'String',forms.CharField),
    )
    name = models.CharField(max_length = 100, verbose_name="Parameter name")
    type = models.CharField(max_length = 50, choices=[(i[0],i[1]) for i in ALLOWED_TYPES], )#radio_admin=True, )
    command = models.ForeignKey(Command)

    unique_together= (('name','command'),)
  
    def create_instance(self, cmd_exec, value):
        up = UsedParameter()
        up.command=cmd_exec
        up.parameter=self
        up.value=value
        up.save()
        return up

    def get_form_id(self):
        return "param_id_%(id)d" % {'id':self.id}

    def to_input(self):
        return "<tr><td><label for='%(form_id)s'>%(name)s</label></td><td><input type='text' name='%(form_id)s' /></td></tr>" % {'form_id':self.get_form_id(), 'name':self.name }

    def to_field(self):
        for t in self.ALLOWED_TYPES:
            if self.type == t[0]:
                return t[2]()
        return forms.Field() 

#FIXME Was this used?
#validate_ap_or_group = validators.RequiredIfOtherFieldNotGiven("group","Besoin du groupe ou du AP")

class CommandExec ( models.Model ):
    command = models.ForeignKey(Command)
    accesspoint = models.ForeignKey(AccessPoint,null=True,)#FIXME See above validator_list=(validate_ap_or_group,))
    group = models.ForeignKey(APGroup,null=True)
    last_run = models.DateTimeField(null=True)

    def get_absolute_url(self):
        return reverse("apmanager.accesspoints.views.apcommands.view_command", args=(self.id,))

    def target(self):
        return self.group or self.accesspoint

    def target_list(self):
        if self.group:
            return self.group.accessPoints.all()
        else:
            return [self.accesspoint,]

    def __target_table_row(self):
        if self.group:
            return '<a href="%s">%s</a>' % (self.group.get_absolute_url(),self.group.name)
        else:
            return '<a href="%s">%s</a>' % (self.accesspoint.get_absolute_url(),self.accesspoint.name) 

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in (
            'Commande','Cible','Dernier lancement',#'R&eacute;ussi','Cr&eacute;&eacute;',
           # 'D&eacute;but&eacute;', 'Termin&eacute;',
        )])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="%s">%s</a>' % (self.get_absolute_url(),self.command.name),
            self.__target_table_row(),
			self.last_run,
           # self.result == 0,self.created, self.started, self.ended,
        )])

    def schedule(self):
        for target in self.target_list():
            cer, created = CommandExecResult.objects.get_or_create(commandexec=self,accesspoint=target, defaults={'created':datetime.now()})
            cer.schedule()
        self.last_run = datetime.now()
        self.save()


class CommandExecResult ( models.Model ):
    SCP_COMMAND="scp -Bq -o StrictHostKeyChecking=no %(filename)s %(ip_addr)s:%(path)s"
    EXEC_COMMAND="ssh -o BatchMode=yes -o StrictHostKeyChecking=no %(ip_addr)s . /tmp/_remote_script_wrapper.sh "
    commandexec = models.ForeignKey(CommandExec)
    accesspoint = models.ForeignKey(AccessPoint)
    result = models.IntegerField(null=True)
    output = models.TextField(null=True)
    created = models.DateTimeField()
    started = models.DateTimeField(null=True)
    ended = models.DateTimeField(null=True)

    def get_absolute_url(self):
        return reverse("apmanager.accesspoints.views.apcommands.view_exec", args=(self.id,))

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in (
            'AP','R&eacute;ussi','Cr&eacute;&eacute;',
            'D&eacute;but&eacute;', 'Termin&eacute;', '',
        )])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="%s">%s</a>' % (self.accesspoint.get_absolute_url(),self.accesspoint.name),
            self.result == 0,self.created, self.started, self.ended,
            '<a href="%s">%s</a>' % (self.get_absolute_url(),'D&eacute;tails'),
        )])

    def schedule(self):
        #Mark as started
        self.started = datetime.now()
        self.status = None
        self.ended = None
        self.output = ''
        self.save()
        #write a new file with this commandexec's id in the watched dir
        file(os.path.join(settings.COMMAND_WATCH_DIR,str(self.id)),'w').close()
        
    def execute(self):
        #Make params file
        (fd, name) = mkstemp()        
        fdo = os.fdopen(fd,'w')
        fdo.write("#!/bin/sh\n")
        fdo.writelines([p.to_bash() for p in self.commandexec.usedparameter_set.all()])
        fdo.write("\n")
        if not self.commandexec.command.script:
            fdo.write(self.commandexec.command.script_text)
        else:
            fdo.write(". /tmp/_remote_script.sh \n")

        fdo.flush()
        fdo.close()

        #scp params to ap
        scp = self.SCP_COMMAND % {
            "filename":name,
            "ip_addr":self.accesspoint.ipv4Address,
            "path":"/tmp/_remote_script_wrapper.sh",
        }
        (ret, output) = commands.getstatusoutput(scp)

        if ret!= 0:
            self.output = output or "SCP Failed"
            self.ended = datetime.now()
            self.result = ret
            self.save()
            return
 
        if self.commandexec.command.script:
            #scp script to ap
            scp = self.SCP_COMMAND % {
                "filename":self.commandexec.command.script,
                "ip_addr":self.accesspoint.ipv4Address,
                "path":"/tmp/_remote_script.sh",
            }
            (ret, output) = commands.getstatusoutput(scp)

            if ret!= 0:
                self.output = output or "SCP Failed"
                self.ended = datetime.now()
                self.result = ret
                self.save()
                return
      
        #exec script on ap 
        exec_cmd = self.EXEC_COMMAND % {
            "ip_addr":self.accesspoint.ipv4Address,
        } 
        
        (ret, output) = commands.getstatusoutput(exec_cmd)
    
        self.output = output
        self.result = ret
        self.ended = datetime.now()
        self.save()
        return

class UsedParameter ( models.Model ):
    parameter = models.ForeignKey(CommandParameter)
    command = models.ForeignKey(CommandExec)
    value = models.TextField()
    
    unique_together = (('parameter','command'),)
    def to_bash(self):
        return "%s=%s\n" % (self.parameter.name,self.value)
