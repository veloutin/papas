import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
HERE = os.path.dirname(__file__)
sys.path.append(os.path.join(HERE, "apmanager"))
sys.path.append(os.path.join(HERE, "lib"))

from lib6ko import *
