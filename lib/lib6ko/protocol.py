import re
from gettext import gettext as _
from operator import attrgetter

import commands
import logging
import pexpect

from lib6ko import parameters as _P

_LOG = logging.getLogger("protocol")

class ScopedDict(dict):
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
            return attrgetter(name)(source)
        except (KeyError, AttributeError):
            if default is None:
                raise MissingParametersException(_("%s is a required parameter") % name)
            else:
                return default
            
    def require_parameter(self, name, default=None):
        return self.require("param::" + name, default)

class ConsoleProtocol(Protocol):
    LOGIN_PROMPT = re.compile(r"(username|login) ?:", re.I)
    FAILURE = re.compile(r"failed", re.I)
    CLOSED = re.compile(r"closed", re.I)
    PROMPT = re.compile(r"(>|#)")
    ROOT_PROMPT = re.compile(r"#")

    """ Console Protocol """
    def __init__(self, parameters):
        super(ConsoleProtocol, self).__init__(parameters)
        self.child = None
        self.EXIT_CMD = self.require_param(
            _P.CONSOLE_EXIT,
            default="exit",
            )
    
    @property
    def connected(self):
        return self.child is not None

    def disconnect(self):
        if not self.connected:
            _LOG.warn("Already Disconnected")
            return

        _LOG.info("Disconnecting")
        self.child.sendline(self.EXIT_CMD)
        index = self.child.expect([
                self.CLOSED,
                pexpect.EOF,
                pexpect.TIMEOUT,
            ], timeout = 15 )

        self.child.close()
        self.child = None
        
    def execute_text(self, text):
        #Consume previous text
        self.child.expect([self.PROMPT, pexpect.TIMEOUT], timeout=0)

        #Send lines
        for line in text.splitlines():
            self.child.sendline(line)

    def send_if_no_echo(self, text):
        self.child.waitnoecho(0)
        self.child.sendline(text)


class MissingParametersException(Exception):
    """ Missing Parameters to use Protocol """

class TemporaryFailure(Exception):
    """ Temporary failure to use Protocol, possible to try again """

class PermanentFailure(Exception):
    """ Permanent failure, do not try again with same parameters """

def iter_by(iterable, count):
    gen = iter(iterable)
    try:
        while True:
            yield [gen.next() for i in xrange(count)]
    except StopIteration:
        return

class SNMPProtocol(Protocol):
    """ SNMP Protocol """
    TYPES = "iusxdnotab="
    RES_RE = re.compile("^(?P<oid>.*) = (?P<type>[A-Z]*): (?P<value>.*)$")
    def __init__(self):
        self._host = None
        self._community = None

    def init(self, parameters):
        self._host = self.require("ap::ipv4Address")
        self._community = self.require_param(_P.SNMP_COMMUNITY)

    def get_common_options(self):
        raise NotImplementedError("Base SNMP Protocol must be extended")

    def _make_set_value(self, oid, t, value):
        if len(t) > 1 or not t in self.TYPES:
            return None
        return "%s %s %s" % (oid.replace("'", ""), t, value.replace("'", ""))

    def set_value(self, *args):
        """ set_value(oid, type, value, [oid, type, value]*) """
        alen = len(args)
        if alen < 3:
            raise TypeError("set_value takes at least 3 argument (%d given)" % alen)
        elif alen % 3 != 0:
            raise TypeError("Invalid number of arguments, not a multiple of 3")
        
        cmd = "snmpset %(common)s %(oid)s" % dict(
            common = self.get_common_options(),
            oid = " ".join(
                [ self._make_set_value( oid, t, value ) for
                    (oid, t, value) in iter_by(args, 3)
                ])
        )
        ret, out = commands.getstatusoutput(cmd)

    def _extract_value(self, line):
        match = self.RES_RE.match(line)
        if match:
            return (match.group("oid"), match.group("value"))
        else:
            return None
    
    def get_values(self, *oids):
        """ get_value(oid, [oid, ...]) """
        if len(oids) == 0:
            raise TypeError("get_value takes at least 1 argument (0 given)")
        cmd = "snmpget %(common)s %(oid)s" % dict(
            common = self.get_common_options(),
            oid = " ".join([oid.replace("'","") for oid in oids])
        )
        ret, out = commands.getstatusoutput(cmd)
        if ret != 0:
            print ret, out
            raise Exception("Failed to get value")

        return dict(
                ( self._extract_value(line) for line in out.splitlines() ),
            )

