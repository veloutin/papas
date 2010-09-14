import os
import sys

CONFIG_DIR = '/etc/papas'
sys.path.append(CONFIG_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

