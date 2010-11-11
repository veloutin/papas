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
