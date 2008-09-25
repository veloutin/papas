# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import user_passes_test
from apmanager.multireport.models import MultiReport
from apmanager.genericsql.models import Report, ColumnName, ReportFooter
from apmanager.genericsql.views import *
from apmanager.genericsql.views import _convert_data,_get_footer_or_none,_do_sort,_get_column_iter

from django.contrib.auth import LOGIN_URL
from django.conf import settings 
SITE_PREFIX_URL = settings.SITE_PREFIX_URL

login_required = user_passes_test(lambda u: u.is_authenticated(), ("/"+SITE_PREFIX_URL+LOGIN_URL).replace("//","/"))


@login_required
def display_multireport(request,multireport_id):
    """
        Attempts to display the multireport
    """
    multireport = get_object_or_404(MultiReport,pk=multireport_id)
    report = multireport.report_parameter.report

    #Test Report Access
    if not report.verify_user_access(request.user.username):
        return render_to_response('genericsql/access_denied.html',{})

    #Sort the report if sortable
    allow_sort=False
    if report.has_sort():
        allow_sort=True
        _do_sort(report,request)

    #get report_data
    db = GenericDbProxy(report.data_source)
    
    #get all arguments to be passed on to the sql query
    sel_args = report.get_args(request)
     

    #Now, we must fetch all the reports
    param_values = []
    try:
        param_values = [r[0] for r in db.select(multireport.param_values,{})]
        
    except ProgrammingError,e:
        return render_to_response('genericsql/report_error.html',
            {"exception":e})
    report_list = []
    for param in param_values:
        #update the sel args with the param
        rsel_args = sel_args
        rsel_args.update({multireport.report_parameter.name:param})
        
        try:
            result = db.select(report.sql,sel_args)
        except (KeyError,ProgrammingError),e:
            report_list.append({"title":report.title%(sel_args),
                   "html":render_to_string('genericsql/report_error.html',
                       {"exception":e})})
            continue 

        column_list = db.get_column_list()
        db.commit()


        # Transfert des réultats SQL, en effectuant une 
        # conversion unicode et en appliquant le filtre de données
        display_data = _convert_data(report,result,column_list)

        #Get the footer
        report_footer = _get_footer_or_none(report,display_data,column_list)
     
        # Renomme les colonnes
        # FIXME: pas efficient
        for c in ColumnName.objects.filter(Q(report=report)|Q(report__isnull=True)):
            for dcl in column_list:
                if c.sql_column_name == dcl:
                    index = column_list.index(dcl)
                    column_list[index] = c.display_column_name
     
        

        #Create a context dictionary
        context = {'report':report,
                 'result':display_data,   
                 'column_list':column_list,
		 'printable':request.GET.has_key('imprimer'),
                 'report_footer':report_footer}
 
        report_list.append({"title":report.title % sel_args,
                "html":render_to_string('genericsql/report_data.inc.html',context)
             })

    return render_to_response('multireport/report_list.html',{
                'report_list':report_list,
                'report':report,
                'printable':request.GET.has_key('imprimer')})






@login_required
def display_multireport_list(request):
    """
        Displays the list of all multireports available
        for the authenticated user 
    """
    reports_all=MultiReport.objects.all().order_by('name')
    reports=[]
    for report in reports_all:
        if report.report_parameter.report.verify_user_access(request.user.username):
            reports.append(report)
    return render_to_response('multireport/multireport_list.html',
        {'object_list':reports,})




