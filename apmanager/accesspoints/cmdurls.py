
from django.conf.urls.defaults import *

urlpatterns = patterns ('apmanager.accesspoints',


    (r'new/$', 'views.apcommands.create_new_command' ),

    (r'new/ap/(?P<ap_id>\d+)/cmd/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' , {'group_id':None} ),
    (r'new/cmd/(?P<command_id>\d+)/ap/(?P<ap_id>\d+)/$', 'views.apcommands.edit_new_command' , {'group_id':None} ),

    (r'new/group/(?P<group_id>\d+)/cmd/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' , {'ap_id':None} ),
    (r'new/cmd/(?P<command_id>\d+)/group/(?P<group_id>\d+)/$', 'views.apcommands.edit_new_command' , {'ap_id':None} ),

    (r'view/(?P<command_id>\d+)/$','views.apcommands.view_command'),
    (r'viewexec/(?P<exec_id>\d+)/$','views.apcommands.view_exec'),

    (r'$', 'views.apcommands.view_home' ),


)
