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

# -*- coding: UTF-8 -*-
from django.utils.translation import ugettext as _
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group#,User #possible accès User
from django.conf import settings
INSTALLED_APPS = settings.INSTALLED_APPS

LDAP_CONNECTOR=False
if 'apmanager.ldapconnector' in INSTALLED_APPS:
    from apmanager.ldapconnector.models import LDAPGroup
    LDAP_CONNECTOR=True
from decimal import Decimal

DATABASE_CHOICE = (
    ('MY', 'MySQL'),
    ('PG', 'PostgreSQL'),
)

ENCODING_CHOICE = (
    ('8859', 'ISO-8859-1'),
    ('UTF8', 'Unicode'),
)


class DataSource(models.Model):
    name = models.CharField(max_length = 100, unique=True, 
        help_text=u"A name to easily identify this data source in the administration interface.")
    database_name = models.CharField(max_length = 30, 
        help_text=u"The name of the database containing the data for the report.")
    database_type = models.CharField(max_length = 2, choices = DATABASE_CHOICE)
    host = models.CharField(max_length = 100)
    port = models.PositiveIntegerField(
        help_text=u"Leave blank to use default port.", blank=True, null=True)
    user = models.CharField(max_length = 100)
    password = models.CharField(max_length = 100, 
        help_text=u"<strong>Warning</strong> : the password will appear in clear text at the screen.")
    data_encoding = models.CharField(max_length = 4, choices = ENCODING_CHOICE,
        help_text=u"""Indicates the native data format of the database.
            Change this setting if accents are incorrectly displayed for this data source.""")
    def __unicode__(self):
        return self.name

class Report(models.Model):
    title = models.CharField(max_length = 300)
    data_source = models.ForeignKey(DataSource)
    owner = models.CharField(max_length = 150, blank=True, null=True,
        help_text=u"The name of the person maintaining this report.")
    sql = models.TextField()
    data_filter = models.CharField(max_length = 150, blank=True, null=True,
        help_text=u"""A Python function to call to alter the data.
            The parameters to the function are : sql_column_name, data.
            You must include the full module path to the function, ex:
            apmanager.contrib.datafilters.rt_ticket_link""")
    
    if LDAP_CONNECTOR: 
        allowed_groups = models.ManyToManyField(LDAPGroup,filter_interface=True, null=True, blank=True)
    
    default_order_by = models.CharField(max_length = 150, null=True, blank=True,
        help_text=u"""The default sorting for the results.
            the keyworks ORDER BY are NOT to be included in this field.
            ex: for ORDER BY 1,2 DESC, the value would be "1,2 DESC" """)
            
    def has_sort(self):
        if self.default_order_by not in [None,""]:
            #there is an order by, verify the query formation
            import re
            #Query must finish with ORDER BY, and possibly a semi-colon and spaces afterwards
            return re.compile("ORDER BY\s*(LIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*)?;?\s*$").search(self.sql) is not None
        return False

    def get_args(self,request):
        """
            Gets sql args from:
                1) the default report parameter values
                2) the GET request
        """
        sel_args = {}
        for param in self.reportparameter_set.all():
            #first get all the default parameter values
            sel_args[param.name] = param.defaultvalue
        for key,val in request.GET.items():
            #now get all parameters supplied from the GET
            sel_args[key] = val
        return sel_args

    def __unicode__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("apmanager.genericsql.views.display_report", args=(self.id,))
    def has_footers(self):
        return self.reportfooter_set.count()>0
    
    def get_multireports(self):
        #First, get all reportparameters
        rparams=self.reportparameter_set.all()
        ret = []
        for rp in rparams:
            #Report has multireports
            if hasattr(rp,'multireport_set'): 
                ret.extend(rp.multireport_set.all())

        return ret

    
    if LDAP_CONNECTOR:
        def verify_user_access(self,username):
            allowed_groups = self.allowed_groups.all()
            if allowed_groups:
                #Verify that the user can access the report
                if not LDAPGroup.objects.user_in_groups(username,allowed_groups):
                    #access DENIED!!!!
                    return False
            else:
                return True
    else:
        def verify_user_access(self,username):
            return True
            
class ReportParameter(models.Model):
    name = models.CharField(max_length = 50, verbose_name=u"Parameter name")
    defaultvalue = models.CharField(max_length = 300, verbose_name=u"Default value")
    report = models.ForeignKey(Report)
    display_name = models.CharField(null=True,blank=True,max_length = 100, verbose_name=u"Display name")
    display = models.BooleanField(default=False, verbose_name=u"Show in parameter panel")
    
    def __unicode__(self):
        return u"%s=%s" % (self.name, self.defaultvalue)

   
    def str_report(self):
        return "%s: %s" % (self.report.title, self.name)
    
    def option_dict(self):
        """Return this report parameter as a dictionary suitable
            for using in the report param panel"""
        ret = {'name':str(self.name),
                'display_name':str(self.display_name or self.name),
                'param_name':str(self.name)}
        if self.defaultvalue:
            ret['value'] = str(self.defaultvalue)
            ret['enabled'] = True
        
        return ret

    class Meta:
        verbose_name = "Default report parameter"
        ordering = ['report','name']
    
class ColumnName(models.Model):
    report = models.ForeignKey(Report, null=True,blank=True)
    sql_column_name = models.CharField(max_length = 40)
    display_column_name = models.CharField(max_length = 100)
    def __unicode__(self):
        return self.display_column_name

class ReportFooter(models.Model):
    report = models.ForeignKey(Report)
    column_name= models.CharField(max_length = 40, )
    function = models.PositiveSmallIntegerField(blank=True, verbose_name=_(u'Agregate function to perform'),
        choices=((0, 'None'),
                 (1, 'Addition'),
                 (2, 'Average'),
                 (3, 'Count')))
    label = models.CharField(max_length = 100,blank=True)
    
    def render(self,values_iter):
        if self.function == 1:  # Addition
            sum = Decimal()
            for i in values_iter:
                sum += Decimal(str(i))
                
            #Prepend label+":" if label not blank
            if self.label == "":
                return sum
            else:
                return "%s&nbsp;: %s" % (self.label, sum)
            
        elif self.function == 2: # Moyenne
            sum,count=Decimal(),Decimal()
            for i in values_iter:
                sum += Decimal(str(i))
                count += 1
            try:
                val = sum/count
            except ZeroDivisionError:
                val = "0"
                
            #Prepend label+":" if label not blank
            if self.label == "":
                return val
            else:
                return "%s&nbsp;: %s" % (self.label, val)
        elif self.function == 3: # Count
            count=Decimal()
            for i in values_iter:
                count += 1
            
            #Prepend label+":" if label not blank
            if self.label == "":
                return count
            else:
                return "%s&nbsp;: %s" % (self.label, count)
        else:
            return self.label

