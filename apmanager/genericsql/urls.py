from django.conf.urls.defaults import *

# Report list
urlpatterns = patterns('apmanager.genericsql',
    (r'^$', 'views.display_report_list'), # genericsql/report_list.html
)

# Application specific views
urlpatterns += patterns('apmanager.genericsql',
    (r'^(?P<report_id>\d+)/$', 'views.display_report'),
)
