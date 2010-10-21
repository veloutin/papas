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
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

@login_required
def view_ap_list(request):
    """
        Displays the list of all access points 
    """
    ap_list=AccessPoint.objects.all().order_by('name')
    return render_to_response('accesspoints/list.html',
        {'object_list':ap_list,
         'caption':_("Access Point list"),
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
    
    return HttpResponse("%(name)s;%(ip)s;;ap;\n" % {
                            'name':ap.name,
                            'ip':ap.ipv4Address,
                            },
                        mimetype="text/plain",
                        )

def view_nagios_config(request):
    """
        Display the nagios config for all access points
    """
    return HttpResponse("".join(
                    ["%(name)s;%(ip)s;;ap;\n" % {
                        'name':ap.name,
                        'ip':ap.ipv4Address,
                        } for ap in AccessPoint.objects.all() ]
                ),mimetype="text/plain")

def get_init_status(arch_init_list, ap_init_list):
    success = []
    error = []
    missing = []
    
    #Load the ap's init sections in a dict by (unique) section name
    ap_init = dict(
        (
            (init_sect.section.section.name, init_sect)
            for init_sect in ap_init_list
        ),
    )

    #Find out what sections of the architecture init are missing, or in error
    for ins in arch_init_list:
        if not ins.section.name in ap_init:
            missing.append(ins)
        elif ap_init[ins.section.name].status != 0:
            error.append(ap_init[ins.section.name])
        else:
            success.append(ap_init[ins.section.name])
        
    return dict(
        success = success,
        missing = missing,
        error = error,
        )

@login_required
def ap_init_overview(request):
    if request.method == "POST":
        if request.POST.has_key("ap_all"):
            aps = AccessPoint.objects.all()
        elif request.POST.has_key("ap_id"):
            aps = AccessPoint.objects.filter(id__in=request.POST.getlist("ap_id"))
        else:
            return HttpResponseRedirect(reverse(ap_init_overview))

        for ap in aps:
            ap.schedule_init()
            return render_to_response('redirect.html',
                {'url':reverse(ap_init_overview),
                 'time':60
                },
                context_instance=RequestContext(request))
    aps = AccessPoint.objects.all()
    arch_init_sections = {}
    res = []
    for ap in aps:
        #Do not fetch the init sections for each architecture more than once
        if ap.architecture.id in arch_init_sections:
            init_sections = arch_init_sections[ap.architecture.id]
        else:
            init_sections = arch_init_sections.setdefault(
                ap.architecture.id,
                ap.architecture.initsection_set.order_by('section__name'),
                )

        init_status = get_init_status(
            init_sections,
            ap.archinitresult_set.all(),
            )

        # Check if there is an init output for
        res.append(dict(
            ap = ap,
            missing = len(init_status["missing"]),
            error = len(init_status["error"]),
            success = len(init_status["success"]),
            )
        )

    return render_to_response("accesspoints/init_overview.html",
        dict(
            ap_list=res,
        ),
        context_instance=RequestContext(request),
        )

@login_required
def view_ap_init(request, ap_id):
    ap = get_object_or_404(AccessPoint, pk=ap_id)

    init_status = get_init_status(
        ap.architecture.initsection_set.order_by('section__name'),
        ap.archinitresult_set.all(),
        )

    if request.method=='POST':
        ap.schedule_init()
        return render_to_response('redirect.html',
            {'url':reverse(view_ap_init,kwargs={'ap_id':ap.id}),
             'time':30,
            },
            context_instance=RequestContext(request))
    return render_to_response('accesspoints/ap.html',
        {'ap':ap,
         'init_status':init_status,},
        context_instance=RequestContext(request))

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
         'caption':_('List of Clients'),
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

