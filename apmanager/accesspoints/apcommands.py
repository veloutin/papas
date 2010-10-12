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

import traceback

from django.utils.translation import ugettext as _

from django.db import models
from django.core.urlresolvers import reverse
from django import forms
from django.conf import settings
from django.template import Context

from apmanager.accesspoints.models import (
    AccessPoint,
    APGroup,
    CommandTarget,
    )

from apmanager.accesspoints.architecture import (
    CommandDefinition,
    Protocol,
    )

from datetime import datetime
import os


class Command ( models.Model ):
    """
        Command to execute on an Access Point.
    """
    name = models.CharField( max_length=255,
        help_text=u"Display Name", unique=True )
    script = models.FileField ( upload_to=settings.UPLOAD_ROOT, blank=True )
    script_text = models.TextField( blank=True)

    class Meta:
        ordering = ('name', )
        verbose_name = _(u"Command")

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
    type = models.CharField(max_length = 50,
        choices=[(i[0],i[1]) for i in ALLOWED_TYPES],
        )#radio_admin=True, )
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
        return "<tr><td><label for='%(form_id)s'>%(name)s</label></td><td><input type='text' name='%(form_id)s' /></td></tr>" % {
            'form_id':self.get_form_id(),
            'name':self.name,
            }

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

    class Meta:
        ordering = ('-last_run', )
        verbose_name = _(u"Command Execution")
        verbose_name_plural = _(u"Command Executions")
        
    def __unicode__(self):
        return _(u"{0.command} on {0.target}").format(self)


    def get_absolute_url(self):
        return reverse("apmanager.accesspoints.views.apcommands.view_command",
            args=(self.id,),
            )

    @property
    def target(self):
        return CommandTarget(self.accesspoint, self.group)

    @property
    def target_list(self):
        return self.target.targets

    def __target_table_row(self):
        return '<a href="%s">%s</a>' % (
            self.target.target.get_absolute_url(),
            self.target.target.name,
            )

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
            cer, created = CommandExecResult.objects.get_or_create(
                commandexec=self,
                accesspoint=target,
                defaults={'created':datetime.now()},
                )
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

    class Meta:
        verbose_name = _(u"Command Execution Result")
        verbose_name_plural = _(u"Command Execution Results")

    def get_absolute_url(self):
        return reverse("apmanager.accesspoints.views.apcommands.view_exec",
            args=(self.id,),
            )

    @staticmethod
    def table_view_header():
        return "".join(["<th>%s</th>" % i for i in (
            _('AccessPoint'),
            _('Status'),
            '',
            'Cr&eacute;&eacute;',
            'D&eacute;but&eacute;',
            'Termin&eacute;',
        )])

    @staticmethod
    def table_view_footer():
        return None

    def to_table_row(self):
        status = _("Unknown")
        if self.started is None:
            status = _("Not started")
        elif self.ended is None:
            status = _("Not ended")
        elif self.result == 0:
            status = _("OK")
        else:
            status = _("Failed")
            
        return "".join(["<td>%s</td>" % i for i in (
            '<a href="%s">%s</a>' % (
                self.accesspoint.get_absolute_url(),
                self.accesspoint.name,
                ),
            status,
            '<a href="%s">%s</a>' % (
                self.get_absolute_url(),
                _("Details"),
                ),
            self.created,
            self.started,
            self.ended,
        )])

    def schedule(self):
        #Mark as started
        self.started = datetime.now()
        self.status = None
        self.ended = None
        self.output = ''
        self.save()

        # Use the daemon if allowed by settings for asynchronous execution
        if settings.USE_DAEMON:
            #write a new file with this commandexec's id in the watched dir
            file(
                os.path.join(
                    settings.COMMAND_WATCH_DIR,
                    str(self.id),
                    ),
                'w',
                ).close()
        else:
            self.execute()
        
    def execute(self):
        #Make params file
        from lib6ko.run import Executer
        from lib6ko.protocol import ScriptError
        params = self.accesspoint.get_param_dict()
        for up in self.commandexec.usedparameter_set.all():
            params[up.name] = up.value

        executer = Executer(Protocol.objects.all())

        # Get the good command implementation
        impl = self.commandexec.command.get_implementation(self.accesspoint)
        if impl is None:
            self.output = "No implementation for command"
            self.result = -1
            self.ended = datetime.now()
            self.save()
            return

        # Execute
        try:
            self.output = executer.execute_template(
                impl.compile_template(),
                self.accesspoint,
                params,
                context_factory=Context,
                )
            self.result = 0
        except ScriptError, e:
            self.output = e.traceback
            self.result = -1
        except Exception, e:
            self.output = traceback.format_exc()
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
        unique_together = (
            ('name','command'),
            )
