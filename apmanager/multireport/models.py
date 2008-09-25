# -*- coding: UTF-8 -*-
from django.db import models
from apmanager.genericsql.models import Report, ReportParameter
from apmanager.urls import prefix
from django.conf import settings
from django.core import validators

def get_report_param_choices():
    res = []
    for rp in ReportParameter.objects.all():
        res.append((rp.id,rp.str_report()))
    return res

class MultiReport(models.Model):
    name = models.CharField(maxlength = 255)
    report_parameter = models.ForeignKey(ReportParameter,choices=get_report_param_choices())
    param_values = models.TextField(help_text="A SQL Query to run on the report's database for which the first column will be used as a series of parameters for the multireport")

    def __str__(self):
        return "%s (%s)"%(self.name, self.report_parameter.str_report())
    def get_absolute_url(self):
        return prefix("/multireport/%i/" % self.id,settings.SITE_PREFIX_URL)
    class Admin:
        pass
    

