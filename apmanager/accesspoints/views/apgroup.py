from apmanager.accesspoints.models import *
from apmanager.settings import SITE_PREFIX_URL
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import LOGIN_URL

login_required = user_passes_test(lambda u: u.is_authenticated(), ("/"+SITE_PREFIX_URL+LOGIN_URL).replace("//","/"))

@login_required
def view_group_list(request):
    """
        Displays the list of all access points 
    """
    group_list=APGroup.objects.all().order_by('name')
    return render_to_response('accesspoints/list.html',
        {'object_list':group_list,
         'caption':'List of AP Groups',
         'table_header':APGroup.table_view_header(),
         'table_footer':APGroup.table_view_footer(),})


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
        'footer':AccessPoint.table_view_footer(),})


