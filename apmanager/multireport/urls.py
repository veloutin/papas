from django.conf.urls.defaults import *

# Report list
urlpatterns = patterns('apmanager.multireport',
    (r'^$', 'views.display_multireport_list'), # genericsql/report_list.html
)

# Application specific views
urlpatterns += patterns('apmanager.multireport',
    (r'^(?P<multireport_id>\d+)/$', 'views.display_multireport'),
)
