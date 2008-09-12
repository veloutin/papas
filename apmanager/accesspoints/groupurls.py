from django.conf.urls.defaults import *

urlpatterns = patterns ('apmanager.accesspoints',

    (r'^$', 'views.apgroup.view_group_list' ),

    (r'^(?P<group_id>\d+)/$', 'views.apgroup.view_group' ),



)
