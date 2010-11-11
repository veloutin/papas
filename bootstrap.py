# PAPAS Access Point Administration System
# Copyright (c) 2010 Revolution Linux inc. <info@revolutionlinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
