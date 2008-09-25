from django.db import models
from apmanager.accesspoints.models import AccessPoint, APGroup
from datetime import datetime
from apmanager import settings
from tempfile import mkstemp
import commands
import os,sys

from django.core import validators

def sleep_and_exit( exit=0, len='5s' ):
    os.system('sleep '+ len)
    return HttpResponseNotModified()
    sys.exit(exit)

validate_file_or_text = validators.RequiredIfOtherFieldNotGiven("script","Vous devez fournir soit un fichier ou du texte comme script")

class Command ( models.Model ):
    """
        Command to execute on an Access Point.
    """
    name = models.CharField( maxlength=255, core=True,
        help_text="Display Name", unique=True )
    script = models.FileField ( upload_to=settings.UPLOAD_ROOT, core=False, blank=True )
    script_text = models.TextField( blank=True, validator_list=(validate_file_or_text,))

    def save(self):
        if self.script_text:
           self.script = ""
        models.Model.save(self)

   
    def __str__(self):
        return "Script: %s" % self.name

    def __repr__(self):
        return "Script: %s [%s]" % (self.name, self.script or self.script_text[0:30])

    class Admin:
        pass
    
    def has_params(self):
        return self.commandparameter_set.count() > 0

    def create_instance(self,target) :
        if isinstance( target, AccessPoint ):
            return self.__create_instance(target)
        elif isinstance( target, APGroup ):
            return [self.__create_instance(ap) for ap in target.accessPoints]
        else:
            raise NotImplementedError("command creation not implemented on objects of type %s" % type(target))

    def __create_instance ( self, ap ):
        cmd = CommandExec(accesspoint=ap, command=self, created=datetime.now())
        cmd.save()
       
        #Created Elsewhere 
        #for param in self.commandparameter_set.iterator():
        #    p = UsedParameter(parameter=param, command=cmd)
        #    p.save()

        return cmd

import django.newforms as forms
class CommandParameter ( models.Model ):
    ALLOWED_TYPES = (
        (int,'Integer',forms.IntegerField),
        (str,'String',forms.CharField),
    )
    name = models.CharField(core=True, maxlength = 100, verbose_name="Parameter name")
    type = models.CharField(core=True, maxlength = 50, choices=[(i[0],i[1]) for i in ALLOWED_TYPES], )#radio_admin=True, )
    command = models.ForeignKey(Command, edit_inline=models.TABULAR)

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


class CommandExec ( models.Model ):
    SCP_COMMAND="scp -Bq -o StrictHostKeyChecking=no %(filename)s %(ip_addr)s:%(path)s"
    EXEC_COMMAND="ssh -o BatchMode=yes -o StrictHostKeyChecking=no %(ip_addr)s . /tmp/_remote_script_wrapper.sh "
    command = models.ForeignKey(Command)
    accesspoint = models.ForeignKey(AccessPoint)
    result = models.IntegerField(null=True)
    output = models.TextField(null=True)
    created = models.DateTimeField()
    started = models.DateTimeField(null=True)
    ended = models.DateTimeField(null=True)

    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in (
            'Commande','AP','R&eacute;ussi','Cr&eacute;&eacute;',
            'D&eacute;but&eacute;', 'Termin&eacute;',
        )])
    table_view_header = staticmethod(table_view_header)
    def table_view_footer():
        return None
    table_view_footer = staticmethod(table_view_footer)
    def to_table_row(self):
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="/commands/view/%d/">%s</a>' % (int(self.id),self.command.name),
            '<a href="/accesspoints/%d/">%s</a>' % (int(self.accesspoint.id),self.accesspoint.name),
            self.result == 0,self.created, self.started, self.ended,
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
        fdo.writelines([p.to_bash() for p in self.usedparameter_set.all()])
        fdo.write("\n")
        if not self.command.script:
            fdo.write(self.command.script_text)
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
 
        if self.command.script:
            #scp script to ap
            scp = self.SCP_COMMAND % {
                "filename":self.command.script,
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
