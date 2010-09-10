from django.conf.urls.defaults import *

urlpatterns = patterns ('apmanager.accesspoints',

    url(r'^$', 'views.ap.view_ap_list', name="home" ),

    (r'^clients/$', 'views.ap.view_client_list' ),
    
    (r'^(?P<ap_id>\d+)/$', 'views.ap.view_ap' ),

    (r'^init/$', 'views.ap.ap_init_overview' ),

    (r'^(?P<ap_id>\d+)/init/$', 'views.ap.view_ap_init' ),

    (r'^(?P<ap_id>\d+)/nagios/$', 'views.ap.view_ap_nagios_config'),

    (r'^nagios/$', 'views.ap.view_nagios_config'),
)
