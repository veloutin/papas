from django.contrib import admin

from apmanager.genericsql.models import DataSource,\
    Report,\
    ReportParameter,\
    ReportFooter,\
    ColumnName

class ReportParameterInline(admin.TabularInline):
    model = ReportParameter
    extra = 3

class ReportFooterInline(admin.TabularInline):
    model = ReportFooter
    extra = 3

class DataSourceAdmin(admin.ModelAdmin):
    list_display=('name', 'database_name', 'database_type', 'host')
    list_filter=['database_type']

class ReportAdmin(admin.ModelAdmin):
    list_display=('title', 'data_source', 'owner')
    list_filter=['data_source', 'owner']

    inlines = [
        ReportParameterInline,
        ReportFooterInline,
    ]


class ColumnNameAdmin(admin.ModelAdmin):
    list_display=('sql_column_name', 'display_column_name', 'report')
    list_filter=['report']
    
admin.site.register(DataSource, DataSourceAdmin)
admin.site.register(ColumnName, ColumnNameAdmin)
admin.site.register(Report, ReportAdmin)
