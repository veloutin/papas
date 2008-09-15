from apmanager.accesspoints.models import *
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import LOGIN_URL
from apmanager.settings import SITE_PREFIX_URL

login_required = user_passes_test(lambda u: u.is_authenticated(), ("/"+SITE_PREFIX_URL+LOGIN_URL).replace("//","/"))

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import django.newforms as forms #To be changed in a next version

class CommandChoiceForm(forms.Form):
    ap_id = forms.ChoiceField(choices=[(ap.id, ap.name) for ap in AccessPoint.objects.all()],
    )
    command_id = forms.ChoiceField(choices=[(c.id,c.name) for c in Command.objects.all()],
    )
    
class CommandInstanceForm(forms.Form):
    pass


@login_required
def view_home(request):
    """
        Welcome page for command management
    """
    return render_to_response('accesspoints/commands/home.html', {})

@login_required
def create_new_command(request):
    """
        Allows the creation of a new command
    """
    if request.method == "POST":
        #On post, Create form with request data, then validate
        f = CommandChoiceForm(request.POST)
        if f.is_valid():
            #
            cmd = get_object_or_404(Command,pk=f.clean_data['command_id'])
            ap = get_object_or_404(AccessPoint,pk=f.clean_data['ap_id'])
            if cmd.has_params():
                return HttpResponseRedirect(
                    reverse(edit_new_command,kwargs=f.clean_data)
                )
            else:
                instance = cmd.create_instance(ap)
                return HttpResponseRedirect(
                    reverse(view_command,kwargs={'command_id':instance.id})
                )
        else:
            #Redisplay invalid form with data and errors
            f = CommandChoiceForm(request.POST)
            return render_to_response('accesspoints/commands/create.html',{'f':f})

    #Otherwise, Display blank form
    f = CommandChoiceForm()
    return render_to_response('accesspoints/commands/create.html',{'f':f})

@login_required
def edit_new_command(request, ap_id, command_id):
    """
        Allows editing the parameters of a new command
    """
    cmd = get_object_or_404(Command,pk=command_id)
    ap = get_object_or_404(AccessPoint, pk=ap_id)
    if request.method == "POST":
        instance = cmd.create_instance(ap)
        for param in cmd.commandparameter_set.all():
            print UsedParameter.objects.all().count()
            up = param.create_instance(instance,request.POST.get(param.get_form_id(),''))
            #TODO treat errors

        return HttpResponseRedirect(
            reverse(view_command,kwargs={'command_id':instance.id})
        )
        
    
    return render_to_response('accesspoints/commands/edit.html',{
            'param_list':cmd.commandparameter_set.all(),
        })

@login_required
def view_command(request, command_id):
    """
        Allows viewing a command's status
    """
    cmd = get_object_or_404(CommandExec,pk=command_id)
    if request.method == "POST":
        cmd.schedule()

    return render_to_response('accesspoints/commands/view.html',{
            'cmd':cmd,
        })


