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

import re


class BasicShell(object):
    LOGIN_PROMPT = re.compile(r"^(username|login) ?: ?$", re.I | re.M)
    PASSWORD_PROMPT = re.compile(r"^.*password.*: ?$", re.I | re.M)
    FAILURE = re.compile(r"failed", re.I)
    CLOSED = re.compile(r"closed", re.I)
    PROMPT = r".*?[>\$\#] ?$"
    ROOT_PROMPT = r".*?\# ?$"
    

class Architecture(object):
    def __init__(self, shell=BasicShell):
        self.shell = shell()

