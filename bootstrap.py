import logging
import logging.config


###
# Setup sys.path to include proper dirs
# 1. Dev tree
# 2. User/Client tree
# 3. Global tree
# construct config dict

import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
HERE = os.path.dirname(__file__)
sys.path.append(os.path.join(HERE, "apmanager"))
sys.path.append(os.path.join(HERE, "lib"))
sys.path.append(os.path.join(HERE, "etc", "papas"))

# Got put config in packaging under papas
# ./config/
# /etc/papas/config
# build config into etc/config
logging.config.fileConfig(os.path.join(HERE, "config", "logging.conf"))

from lib6ko import *

from django.template import Template, Context
from accesspoints.models import *
from lib6ko.protocols.telnet import *
from lib6ko.run import *
