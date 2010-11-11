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

from apmanager.accesspoints.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse

@login_required
def view_group_list(request):
    """
        Displays the list of all groups 
    """
    group_list=APGroup.objects.all().order_by('name')
    return render_to_response('accesspoints/list.html',
        {'object_list':group_list,
         'caption':_(u"Groups List"),
         'table_header':APGroup.table_view_header(),
         'table_footer':APGroup.table_view_footer(),},
        context_instance=RequestContext(request))


@login_required
def view_group(request, group_id):
    """
        Attempts to display the access point with the id ap_id
    """
    group = get_object_or_404(APGroup, pk=group_id)

    return render_to_response('accesspoints/group.html',
        {'group':group,
        'ap_list':group.accessPoints.all(),
        'header':AccessPoint.table_view_header(),
        'footer':AccessPoint.table_view_footer(),},
        context_instance=RequestContext(request))


def view_group_nagios_config(request, group_id):
    """
       Display the access point with the id ap_id's nagios config
    """
    group = get_object_or_404(APGroup, pk=group_id)
    
    return HttpResponse("".join(
                    ["%(name)s;%(ip)s;;ap;\n" % {
                        'name':ap.name,
                        'ip':ap.ipv4Address
                        } for ap in group.accessPoints.all() ]
                ),mimetype="text/plain")

def view_nagios_config(request):
    """
        Display the nagios config for all access points
    """
    return HttpResponse("".join(
                    ["%(name)s;%(ip)s;;ap;\n" % {'name':ap.name,'ip':ap.ipv4Address} for ap in AccessPoint.objects.all() ]
                ),mimetype="text/plain")
