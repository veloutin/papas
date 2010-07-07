from apmanager.accesspoints.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.core.urlresolvers import reverse

@login_required
def view_ap_list(request):
    """
        Displays the list of all access points 
    """
    ap_list=AccessPoint.objects.all().order_by('name')
    return render_to_response('accesspoints/list.html',
        {'object_list':ap_list,
         'caption':"Liste des points d'acc&egrave;s",
         'table_header':AccessPoint.table_view_header(),
         'table_footer':AccessPoint.table_view_footer(),},
        context_instance=RequestContext(request))


@login_required
def view_ap(request, ap_id):
    """
        Attempts to display the access point with the id ap_id
    """
    ap = get_object_or_404(AccessPoint, pk=ap_id)
    if request.method=='POST':
        ap.schedule_refresh()
        return render_to_response('redirect.html',
            {'url':reverse(view_ap,kwargs={'ap_id':ap.id}),
             'time':10
            },
            context_instance=RequestContext(request))
    return render_to_response('accesspoints/ap.html',
        {'ap':ap},
        context_instance=RequestContext(request))

def view_ap_nagios_config(request, ap_id):
    """
       Display the access point with the id ap_id's nagios config
    """
    ap = get_object_or_404(AccessPoint, pk=ap_id)
    
    return HttpResponse("%(name)s;%(ip)s;;ap;\n" % {'name':ap.name,'ip':ap.ipv4Address}, mimetype="text/plain")

def view_nagios_config(request):
    """
        Display the nagios config for all access points
    """
    return HttpResponse("".join(
                    ["%(name)s;%(ip)s;;ap;\n" % {'name':ap.name,'ip':ap.ipv4Address} for ap in AccessPoint.objects.all() ]
                ),mimetype="text/plain")


@login_required
def view_client_list(request):
    """
        Lists all connected clients
    """
    client_list=APClient.objects.all().order_by('connected_to')
    if request.method=='POST':
        for ap in AccessPoint.objects.all():
            ap.schedule_refresh()
        return render_to_response('redirect.html',
            {'url':reverse(view_client_list),
             'time':30
            },
            context_instance=RequestContext(request))
    return render_to_response('accesspoints/list.html',
        {'object_list':client_list,
         'caption':'List of Clients',
         'table_header':APClient.table_view_header(),
         'table_footer':APClient.table_view_footer(),
         'add_refresh_button':True,},
        context_instance=RequestContext(request))
    
@login_required
def create_ap(request):
    manipulator = AccessPoint.AddManipulator()

    if request.method == 'POST':
        # If data was POSTed, we're trying to create a new Place.
        new_data = request.POST.copy()

        # Check for errors.
        errors = manipulator.get_validation_errors(new_data)
        manipulator.do_html2python(new_data)

        if not errors:
            # No errors. This means we can save the data!
            new_ap = manipulator.save(new_data)

            # Redirect to the object's "edit" page. Always use a redirect
            # after POST data, so that reloads don't accidently create
            # duplicate entires, and so users don't see the confusing
            # "Repost POST data?" alert box in their browsers.
            return HttpResponseRedirect("/accesspoints/%i/" % new_ap.id)
    else:
        # No POST, so we want a brand new form without any data or errors.
        errors = new_data = {}

    # Create the FormWrapper, template, context, response.
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('accesspoints/create_aps.html', {'form': form},
        context_instance=RequestContext(request))

