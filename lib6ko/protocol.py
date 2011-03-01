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
_LOG = logging.getLogger("lib6ko.protocol")

from operator import attrgetter

class ScopedDict(dict):
    """
    ScopedDict is a special instance of a normal python dict that allows
    accessing its items' attributes via getattr(). If the attribute name given
    to attr contains the scope separator "::", it will be used as a dictionary
    key and the attribute lookup will continue into the found item.

    If the scope given corresponds to another ScopedDict, the lookup is the
    same in that other ScopedDict.  If it corresponds to a dict, a key lookup
    is attempted.  Otherwise, a normal attribute lookup is performed.
    """

    SCOPE_SEP = "::"
    def __getattribute__(self, name):
        scope, split, attrname = name.partition(ScopedDict.SCOPE_SEP)
        if split:
            obj = self[scope]
            if isinstance(obj, ScopedDict):
                #Continue the scope search in ScopedDict's
                return getattr(obj, attrname)
            elif isinstance(obj, dict):
                #Normal dicts will be searched directly for keys
                return obj[attrname]
            else:
                #Everything else, getattr
                return getattr(obj, attrname)
        else:
            return dict.__getattribute__(self, name)
            
    
    def get(self, name, prefix="", default=None):
        if prefix:
            name = self.SCOPE_SEP.join([prefix, name])
        try:
            return attrgetter(name)(self)
        except (KeyError, AttributeError):
            if default is None:
                raise
            else:
                return default


class ScriptError(Exception):
    """ Script failed to execute properly """
    def __init__(self, message, traceback=None):
        super(ScriptError, self).__init__(message)
        self.traceback = traceback
