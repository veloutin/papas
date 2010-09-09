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
