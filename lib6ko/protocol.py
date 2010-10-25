import logging
from gettext import gettext as _
_LOG = logging.getLogger("lib6ko.protocol")

from operator import attrgetter

from lib6ko import parameters as _P


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
            


class Protocol(object):
    """ Base Protocol Object """
    def __init__(self, parameters):
        self.parameters = parameters

    def require(self, name, default=None):
        try:
            return attrgetter(name)(self.parameters)
        except (KeyError, AttributeError):
            if default is None:
                raise MissingParametersException(_("%s is a required parameter") % name)
            else:
                return default
            
    def require_param(self, name, default=None):
        return self.require("param::" + name, default)



class MissingParametersException(Exception):
    """ Missing Parameters to use Protocol """

class TemporaryFailure(Exception):
    """ Temporary failure to use Protocol, possible to try again """

class PermanentFailure(Exception):
    """ Permanent failure, do not try again with same parameters """

class ConnectionLost(TemporaryFailure):
    """ Connection was lost during the execution """

class ScriptError(Exception):
    """ Script failed to execute properly """
    def __init__(self, message, traceback=None):
        super(ScriptError, self).__init__(message)
        self.traceback = traceback
