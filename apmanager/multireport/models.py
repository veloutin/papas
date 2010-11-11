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
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse

from apmanager.genericsql.models import ReportParameter

def get_report_param_choices():
    res = []
    for rp in ReportParameter.objects.all():
        res.append((rp.id,rp.str_report()))
    return res

class MultiReport(models.Model):
    name = models.CharField(max_length = 255)
    report_parameter = models.ForeignKey(ReportParameter)
    param_values = models.TextField(help_text=u"A SQL Query to run on the report's database for which the first column will be used as a series of parameters for the multireport")

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.report_parameter.str_report())
    def get_absolute_url(self):
        return reverse("apmanager.multireport.views.display_multireport", args=(self.id,))

