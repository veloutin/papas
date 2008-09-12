
from django.conf.urls.defaults import *

urlpatterns = patterns ('apmanager.accesspoints',


    (r'new/$', 'views.apcommands.create_new_command' ),

    (r'new/(?P<ap_id>\d+)/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' ),
    (r'new/ap/(?P<ap_id>\d+)/cmd/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' ),
    (r'new/cmd/(?P<command_id>\d+)/ap/(?P<ap_id>\d+)/$', 'views.apcommands.edit_new_command' ),

    (r'view/(?P<command_id>\d+)/$','views.apcommands.view_command'),

    (r'$', 'views.apcommands.view_home' ),


)
