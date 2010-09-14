from django.conf.urls.defaults import *
from django.conf import settings 
from django.contrib import admin

DEBUG = settings.DEBUG

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),


    (r'^accounts/login/', 'django.contrib.auth.views.login' ),
    (r'^accounts/logout/', 'django.contrib.auth.views.logout' ),

    # Access points
    (r'^accesspoints/', include('apmanager.accesspoints.apurls')),
    # DSH Groups
    (r'^groups/', include('apmanager.accesspoints.groupurls')),

    # Commands
    (r'^commands/', include('apmanager.accesspoints.cmdurls')),

    # Application de rapports generiques
    # (r'^rapports/', include('apmanager.genericsql.urls')),
   
    # Multireports
    # (r'^multireport/', include('apmanager.multireport.urls')),

    (r'^$', include('apmanager.accesspoints.apurls')),
)
# This is used to server static content (images and CSS) during development.
# For production, Apache must be configured.
if DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

