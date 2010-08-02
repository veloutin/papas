# -*- coding: UTF-8 -*-
import re

try:
    from MySQLdb import ProgrammingError
except ImportError:
    class ProgrammingError(Exception):
        pass

from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import get_mod_func
from django.db.models import Q
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from django.conf import settings 

from apmanager.genericsql.models import Report, ColumnName, ReportFooter


class GenericDbProxy:
    def __init__(self, data_source):
        if data_source.database_type == "MY":
            import MySQLdb
            port = data_source.port
            if port == None:
                port = 3306 # MySQL default port
            self._db = MySQLdb.connect(
                host=data_source.host, db=data_source.database_name,
                port=port,
                user=data_source.user, passwd=data_source.password)
            self._cursor = self._db.cursor()
        elif data_source.database_type == "PG":
            import psycopg2
            port = data_source.port
            if port == None:
                port = 5432 # PostgreSQL default port
            else:
                port = int(port)
            self._db = psycopg2.connect(
                host=data_source.host, database=data_source.database_name,
                port=port,
                user=data_source.user, password=data_source.password)
            self._cursor = self._db.cursor()
        else:
            raise Exception("Unknow database type: %s" % data_source.database_type)

    def __del__(self):
        self._cursor.close()
        self._db.close()

    def runSQL(self, sql, args = []):
        if args:
            self._cursor.execute(sql, args)
        else:
            self._cursor.execute(sql)
        return self._cursor.rowcount

    def select(self, sql, args = []):
        self.runSQL(sql, args)
        rows = self._cursor.fetchall()
        return rows

    def mogrify(self, sql, args = []):
        """Returns the query with the arguments replaced"""
        #TODO: test if this works on MySQL
        return self._cursor.mogrify(sql,args)

    def commit(self):
        self._db.commit()

    def get_column_list(self):
        column_list = []
        for d in self._cursor.description:
            column_list.append(d[0])
        return column_list


@login_required
def display_report_list(request):
    """
        Displays the list of all reports available
        for the authenticated user 
    """
    reports_all=Report.objects.all().order_by('title')
    reports=[]
    for report in reports_all:
        if report.verify_user_access(request.user.username):
            reports.append(report)
    return render_to_response('genericsql/report_list.html',
        {'object_list':reports,},
        context_instance=RequestContext(request))
        
        
@login_required
def display_report(request, report_id):
    """
        Attempts to display the report corresponding to report_id
    """
    report = get_object_or_404(Report, pk=report_id)
    
    #if the report has access restrictions
    if not report.verify_user_access(request.user.username):
        return render_to_response('genericsql/access_denied.html',{},
        context_instance=RequestContext(request))
            
    #Sort the report if sortable
    allow_sort=False
    if report.has_sort():
        allow_sort=True
        _do_sort(report,request)
                
    #get all arguments to be passed on to the sql query
    sel_args = report.get_args(request)
    
    #get report_data
    db = GenericDbProxy(report.data_source)
    try:
        result = db.select(report.sql,sel_args)
    except (KeyError,ProgrammingError),e:
        return render_to_response('genericsql/report_error.html',{"exception":e},
        context_instance=RequestContext(request)) 
    
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
    
    #Render callback for sorting
    if request.GET.has_key('callback'):
        return render_to_response('genericsql/report_data.table.inner.html',
            {'column_list':column_list, 'result':display_data,'report_footer':report_footer},
        context_instance=RequestContext(request))
            
    #Render CSV document :o
    if request.GET.has_key('csv'):
        if request.GET.has_key('csv_column_headers'):
            display_data.reverse()
            display_data.append(column_list)
            display_data.reverse()
        return _render_csv(report, display_data, request)
    
    #Select appropriate template for iframe rendering
    if request.GET.has_key('iframe'):
        template = "report_iframe.html"
    else:
        template = "report.html"
   
    # Le titre peut avoir des variables, comme le SQL.
    report.title = report.title % sel_args
    map_argstring="?"
    
    #Create a context dictionary
    context = {'report':report,
                'result':display_data,   
                'column_list':column_list,
                'allow_sort':allow_sort,
                'report_footer':report_footer,
                'printable':request.GET.has_key('imprimer'),
        }

    #Add maps if possible
    if hasattr(report,'map_set'):
        for k,v in sel_args.items():
            map_argstring = map_argstring + k + "=" + v + "&"
        context['map_argstring']=map_argstring[:-1]
        context['map_list']=report.map_set.all()

    #Add Panel if possible
    if hasattr(report,'reportparameter_set'):
        #on cree le dictionaire pour le panel
        panel = {'title':'Options du rapport',
                'options':[opt.option_dict() for opt in report.reportparameter_set.all() if opt.display]}
        
        #on ajoute les valeurs si dans les arguments
        for opt in panel['options']:
            if opt['param_name'] in sel_args:
                opt['value']=sel_args[opt['param_name']]

        if panel['options']:
            from django.utils.simplejson.encoder import JSONEncoder
            context['panel'] = JSONEncoder(separators=(',',':')).encode( panel)

    #Render normal/iframe report
    return render_to_response('genericsql/' + template,context,
        context_instance=RequestContext(request))



def _do_sort(report,request):
    """
        Modify the report.sql directly to perform sort operations on 
        a report, according to either the default order by value of
        the report, or an user supplied value from the GET request.
    """
    #Get the default sorting value
    orderby = report.default_order_by
    #See if a non-blank value was supplied
    if request.GET.has_key("order_by") and request.GET["order_by"]:
        #avoid SQL injection, only allow numerics, commas and DESC
        if re.compile("^[\d]+(\sDESC)?(\s?,\s?([\d]+(\sDESC)?))*\s?$").match(request.GET["order_by"]):
            #use valid ORDER BY
            orderby = request.GET["order_by"]
        else:
            #Throw an error. To use the default value instead, replace this line by "pass"
            return render_to_response('genericsql/report_error.html',
                {"exception":ProgrammingError("ORDER BY "+request.GET["order_by"])})
        
    #now we replace the placeholder in the sql query
    report.sql = report.sql.replace("ORDER BY","ORDER BY " + orderby + " ")


def _convert_data(report,result,column_list):
    """
        Apply unicode conversion and data filters to the data in
        result, and return the converted data.
    """
    data_filter_func = None
    if report.data_filter:
        mod_name, func_name = get_mod_func(report.data_filter)
        data_filter_func = getattr(__import__(mod_name, '', '', ['']), func_name)

    display_data=[]
    for row in result:
        display_data_row = []
        i = 0
        for data in row:
            if data_filter_func:
                data = data_filter_func(column_list[i], data)
            if report.data_source.data_encoding == '8859':
                data = unicode(str(data), "iso-8859-1")
            display_data_row.append(data)
            i = i + 1
        display_data.append(display_data_row)
    return display_data


def _get_footer_or_none(report,display_data,column_list):
    """
        Returns the Report Footer object, or None if the
        report has no Report Footers
    """
    report_footer = None
    if report.has_footers():
        report_footer = []
        for i in column_list:
            report_footer.append("")
        
        for foot in report.reportfooter_set.all():
            try:
                colno = column_list.index(foot.column_name) 
            except ValueError:
                pass
            else:
                report_footer[colno] = foot.render(_get_column_iter(display_data,colno))
                    
    return report_footer
                    
                    
def _get_column_iter(table,col_nb):
    """
        Return an iterable generator object
        from a table's column at index col_nb
    """
    for row in table:
        yield row[col_nb]
    return
    

def _render_csv(report,display_data, request):
    """
        Renders the CSV view of a report
    """
    from django.http import HttpResponse
    from django.template import loader, Context
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+re.sub(r'[\\\/\s]+',r'_',report.title)+'.csv'
   
    delimiter= request.GET.get("csv_text_delimiter", "")
    column_separator= request.GET.get("csv_column_separator", ",")
    row_separator= request.GET.get("csv_row_separator", "")
    t = loader.get_template('genericsql/report.csv')
    c = Context({
        'result':display_data,
        'column_separator':column_separator,
        'row_separator':row_separator,
        'text_delimiter':delimiter,
    })
    response.write(t.render(c))
    return response
    
