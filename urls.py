from django.conf.urls.defaults import *
from settings import DEBUG

urlpatterns = patterns('',
    # Example:

    (r'^accounts/login/', 'django.contrib.auth.views.login' ),
    (r'^accounts/logout/', 'django.contrib.auth.views.logout' ),


    
    # Access points
      (r'^accesspoints/', include('cscs.accesspoints.apurls')),
    # DSH Groups
      (r'^groups/', include('cscs.accesspoints.groupurls')),

    # Commands
      (r'^commands/', include('cscs.accesspoints.cmdurls')),

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),

    (r'^$', include('cscs.accesspoints.apurls')),
)
# This is used to server static content (images and CSS) during development.
# For production, Apache must be configured.
if DEBUG:
    urlpatterns += patterns('',
        (r'^cscs/site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'templates/site-media/'}),
    )

