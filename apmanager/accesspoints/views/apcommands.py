import logging
LOG = logging.getLogger('apmanager.accesspoints')

from apmanager.accesspoints.models import *
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings 
from django.template import RequestContext

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.utils.translation import ugettext as _

@login_required
def view_home(request):
    """
    Welcome page for command management
    """
    if request.GET.has_key("all"):
        cexec_list = CommandExec.objects.order_by('-last_run', '-id')
        caption = _(u"List of all command executions")
    else:
        cexec_list = CommandExec.objects.order_by('-last_run', '-id')[:20]
        caption = _(u"List of recent command executions")
    return render_to_response('accesspoints/list.html',
        {'object_list':cexec_list,
         'caption':caption,
         'table_header':CommandExec.table_view_header(),
         'table_footer':CommandExec.table_view_footer(),},
        context_instance=RequestContext(request))

@login_required
def create_new_command(request):
    """
        Allows the creation of a new command
    """
    ap, group = None, None
    ap_id=request.POST.get('ap_id',None)
    if ap_id:
        ap = get_object_or_404(AccessPoint,pk=ap_id)

    group_id=request.POST.get('group_id',None)
    if group_id:
        group = get_object_or_404(APGroup,pk=group_id)

    cmd_id=request.POST.get('command_id',None)

    if request.method == "POST":
        #On post, Create form with request data, then validate
        if (group_id or ap_id) and cmd_id:
            #Attempt to get both objects
            cmd = get_object_or_404(Command,pk=cmd_id)
            if cmd.has_params():
                return HttpResponseRedirect(
                        reverse(edit_new_command,kwargs={'ap_id':ap_id,'command_id':cmd_id,'group_id':group_id})
                )
            else:
                instance = cmd.create_instance(group or ap)
                return HttpResponseRedirect(
                    reverse(view_command,kwargs={'command_id':instance.id})
                )
        else:
            #Redisplay invalid form with data and errors
            return render_to_response('accesspoints/commands/create.html',{'data':request.POST,
                        'cmd_list':Command.objects.all(),
                        'ap_list':AccessPoint.objects.all(),
                        'group_list':APGroup.objects.all(),},
                        context_instance=RequestContext(request))

    #Otherwise, Display blank form
    return render_to_response('accesspoints/commands/create.html',{'data':{},
                        'cmd_list':Command.objects.all(),
                        'ap_list':AccessPoint.objects.all(),
                        'group_list':APGroup.objects.all(),},
                        context_instance=RequestContext(request))

@login_required
def edit_new_command(request, command_id, ap_id=None, group_id=None):
    """
        Allows editing the parameters of a new command
    """
    ap, group = None, None
    if ap_id:
        ap = get_object_or_404(AccessPoint,pk=ap_id)
    if group_id:
        group = get_object_or_404(APGroup,pk=group_id)

    cmd = get_object_or_404(Command,pk=command_id)
    if request.method == "POST" and (ap_id or group_id):
        instance = cmd.create_instance(group or ap)
        for param in cmd.commandparameter_set.all():
            up = param.create_instance(instance,request.POST.get(param.get_form_id(),''))
            #TODO treat errors

        return HttpResponseRedirect(
            reverse(view_command,kwargs={'command_id':instance.id})
        )
        
    
    return render_to_response('accesspoints/commands/edit.html',{
            'param_list':cmd.commandparameter_set.all(),
        },
        context_instance=RequestContext(request))

@login_required
def view_command(request, command_id):
    """
        Allows viewing a command's status
    """
    cmd = get_object_or_404(CommandExec,pk=command_id)
    if request.method == "POST":
        cmd.schedule()

    return render_to_response('accesspoints/commands/view.html',{
			'result_header':CommandExecResult.table_view_header(),
			'result_footer':CommandExecResult.table_view_footer(),
            'cmd':cmd,
        },
        context_instance=RequestContext(request))

@login_required
def view_exec(request, exec_id):
    """
        View a Request Exec Details
    """
    cmd = get_object_or_404(CommandExecResult,pk=exec_id)
    if request.method == "POST":
        cmd.schedule()

    return render_to_response('accesspoints/commands/viewexec.html',{
            'cmd':cmd,
        },
        context_instance=RequestContext(request))


