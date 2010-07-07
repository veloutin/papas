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

