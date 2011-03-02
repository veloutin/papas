# Django settings for apmanager project.
import os
from django.utils.translation import ugettext_lazy as _

DEBUG = True
USE_DAEMON = True
if os.environ.get("USE_DEV_PATHS", None):
    DEV_PATHS = True
else:
    DEV_PATHS = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'papas.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Montreal'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGES = (
    ('fr', _("French")),
    ('en', _("English")),
)
LANGUAGE_CODE = 'fr_CA'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


if DEV_PATHS:
    UPLOAD_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__),
        "uploads",
        )
    )
else:
    UPLOAD_ROOT = '/var/lib/apmanager/uploads/'

#Site prefix to add to relative urls, such as apmanager/ for a site on example.com/apmanager/
# Leave blank if installed on web root
LOGIN_URL = "/accounts/login/"

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
if DEV_PATHS:
    MEDIA_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__),
        "..", "..", "apmanager", 'templates','site-media'),
        )
else:
    MEDIA_ROOT = "/usr/share/apmanager/templates/site-media"

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'apmanager.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(MEDIA_ROOT, "..")),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'apmanager.accesspoints',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

if DEV_PATHS:
    WATCH_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__),"..","..","watch"),
        )
else:
    WATCH_DIR='/var/lib/apmanager/watch'

COMMAND_WATCH_DIR = WATCH_DIR + '/commands'
AP_DIR = WATCH_DIR + '/ap'
AP_REFRESH_WATCH_DIR = AP_DIR + '/refresh'
AP_INIT_WATCH_DIR = AP_DIR + '/init'


LOCALE_PATHS = (
    '/usr/share/apmanager/locale',
    )

if DEV_PATHS:
    LOCALE_PATHS = LOCALE_PATHS + (
        os.path.join(os.path.dirname(__file__), "..", "..", "locale"),
        )
    TEMPLATE_DIRS = TEMPLATE_DIRS + (
        os.path.join(os.path.dirname(__file__), "..", "..", "apmanager"),
        )

    for dpath in ( 
        UPLOAD_ROOT,
        WATCH_DIR, 
            AP_DIR,
                AP_REFRESH_WATCH_DIR,
                AP_INIT_WATCH_DIR,
            COMMAND_WATCH_DIR,
        ):
        if not os.path.isdir(dpath): os.mkdir(dpath)

