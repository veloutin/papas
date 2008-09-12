from django.conf.urls.defaults import *

urlpatterns = patterns ('cscs.accesspoints',

    (r'^$', 'views.ap.view_ap_list' ),

    (r'^clients/$', 'views.ap.view_client_list' ),
    
    (r'^(?P<ap_id>\d+)/$', 'views.ap.view_ap' ),

    (r'^(?P<ap_id>\d+)/nagios/$', 'views.ap.view_ap_nagios_config'),

)
