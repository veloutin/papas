from django.conf.urls.defaults import *
from settings import DEBUG,SITE_PREFIX_URL

def prefix(url,prefix):
    if prefix:
        return url.replace("^","^"+prefix)
    return url

urlpatterns = patterns('',
    # Example:

    (prefix(r'^accounts/login/',SITE_PREFIX_URL),           'django.contrib.auth.views.login' ),
    (prefix(r'^accounts/logout/',SITE_PREFIX_URL),          'django.contrib.auth.views.logout' ),


    
    # Access points
      (prefix(r'^accesspoints/',SITE_PREFIX_URL),           include('apmanager.accesspoints.apurls')),
    # DSH Groups
      (prefix(r'^groups/',SITE_PREFIX_URL),                 include('apmanager.accesspoints.groupurls')),

    # Commands
      (prefix(r'^commands/',SITE_PREFIX_URL),               include('apmanager.accesspoints.cmdurls')),

    # Uncomment this for admin:
     (prefix(r'^admin/',SITE_PREFIX_URL),                   include('django.contrib.admin.urls')),

    (prefix(r'^$',SITE_PREFIX_URL),                         include('apmanager.accesspoints.apurls')),
)
# This is used to server static content (images and CSS) during development.
# For production, Apache must be configured.
if DEBUG:
    urlpatterns += patterns('',
        (prefix(r'^site-media/(?P<path>.*)$',SITE_PREFIX_URL), 'django.views.static.serve', {'document_root': 'templates/site-media/'}),
    )

