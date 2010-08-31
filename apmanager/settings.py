# Django settings for apmanager project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = os.path.join(os.path.dirname(__file__),'apmanager.sqlite')             # Or path to database file if using sqlite3.
DATABASE_USER = 'apmanager'             # Not used with sqlite3.
DATABASE_PASSWORD = 'ExGldsaj3rt0tZQU'         # Not used with sqlite3.
DATABASE_HOST = '10.145.3.200'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'fr_CA'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


#UPLOAD_ROOT = '/var/lib/apmanager/uploads/'
UPLOAD_ROOT = '/root/var/apmanager/uploads/'

#Site prefix to add to relative urls, such as apmanager/ for a site on example.com/apmanager/
# Leave blank if installed on web root
LOGIN_URL = "/accounts/login/"

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'templates','site-media')

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = "/site-media/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = "/media/"

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')@1wt()$4x&&e9c#n&viv-g#k20(p!_ga)s$+4i!*hbdcid$)s'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'apmanager.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "/usr/share/apmanager/",
    os.path.join(os.path.dirname(__file__), "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'apmanager.accesspoints',
    'apmanager.genericsql',
    'apmanager.multireport',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)
#WATCH_DIR='/var/lib/apmanager/watch/'
WATCH_DIR='/home/vvinet/var/apmanager/watch/'
COMMAND_WATCH_DIR=      WATCH_DIR + 'commands/'
AP_REFRESH_WATCH_DIR=   WATCH_DIR + 'refresh_ap/'
