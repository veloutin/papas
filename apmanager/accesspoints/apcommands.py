from django.db import models
from django.core.urlresolvers import reverse
from django import forms

from apmanager.accesspoints.models import (
    AccessPoint,
    APGroup,
    CommandTarget,
    )

from apmanager.accesspoints.architecture import (
    CommandDefinition,
    )

from datetime import datetime
from apmanager import settings
from tempfile import mkstemp
import commands
import os,sys


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

    def create_instance(self, target) :
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

class CommandExec ( models.Model ):
    command = models.ForeignKey(CommandDefinition)
    accesspoint = models.ForeignKey(AccessPoint,null=True,)
    group = models.ForeignKey(APGroup,null=True)
    last_run = models.DateTimeField(null=True)

    def get_absolute_url(self):
        return reverse("apmanager.accesspoints.views.apcommands.view_command", args=(self.id,))

    @property
    def target(self):
        return CommandTarget(self.accesspoint, self.group)

    @property
    def target_list(self):
        return self.target.targets

    def __target_table_row(self):
        return '<a href="%s">%s</a>' % (self.target.target.get_absolute_url(), self.target.target.name)

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
        for target in self.target_list:
            cer, created = CommandExecResult.objects.get_or_create(commandexec=self,accesspoint=target, defaults={'created':datetime.now()})
            cer.schedule()
        self.last_run = datetime.now()
        self.save()


class CommandExecResult ( models.Model ):
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
        from lib6ko.run import Executer
        params = self.accesspoints.get_param_dict()
        executer = Executer(params)

        # Get the good command implementation
        impl = self.command.get_implementation(ap)
        if impl is None:
            self.output = "No implementation for command"
            self.result = -1
            self.ended = datetime.now()
            self.save()
            return

        # Execute
        try:
            self.output = executer.execute_template(impl.template, ap, params)
            self.result = 0
        except Exception, e:
            self.output = str(e)
            self.result = -1

        self.ended = datetime.now()
        self.save()
        return

class UsedParameter ( models.Model ):
    # parameter = models.ForeignKey(CommandParameter)
    name = models.CharField(max_length=250)
    command = models.ForeignKey(CommandExec)
    value = models.TextField()
    
    class Meta:
        # unique_together = (('parameter','command'),)
        unique_together = (('name','command'),)
    def to_bash(self):
        return "%s=%s\n" % (self.parameter.name,self.value)
