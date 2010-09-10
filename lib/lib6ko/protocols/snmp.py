import logging
from gettext import gettext as _
_LOG = logging.getLogger("protocols.snmp")

import re
import commands

from lib6ko import parameters as _P
from lib6ko.protocol import Protocol, ScriptError

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
    def __init__(self, parameters):
        super(SNMPProtocol, self).__init__(parameters)
        self.host = self.require("ap::ipv4Address")
        self.community = self.require_param(_P.SNMP_COMMUNITY)

    def get_common_options(self):
        raise NotImplementedError("Base SNMP Protocol must be extended")

    def _make_set_value(self, oid, t, value):
        if len(t) > 1 or not t in self.TYPES:
            return None
        return "%s %s %s" % (oid, t, value.replace("'", r"\'"))

    def set_value(self, *args):
        """ set_value(oid, type, value, [oid, type, value]*) """
        alen = len(args)
        if alen < 3:
            raise TypeError(_("set_value takes at least 3 argument (%d given)") % alen)
        elif alen % 3 != 0:
            raise TypeError(_("Invalid number of arguments, not a multiple of 3"))
        
        cmd = "snmpset %(common)s %(oid)s" % dict(
            common = self.get_common_options(),
            oid = " ".join(
                [ self._make_set_value( oid, t, value ) for
                    (oid, t, value) in iter_by(args, 3)
                ])
        )
        _LOG.debug(_("Executing: {0}").format(cmd))
        ret, out = commands.getstatusoutput(cmd)
        if ret != 0:
            raise ScriptError(_("Failed to set value"), out)
        return out

    def _extract_value(self, line):
        match = self.RES_RE.match(line)
        if match:
            return (match.group("oid"), match.group("value"))
        else:
            _LOG.debug(_("Unable to match extract value from line: {0}").format(repr(line)))
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
            raise ScriptError("Failed to get value", out)

        return dict(
                ( filter(None, 
                    (self._extract_value(line) for line in out.splitlines() )
                    )
                ),
            )

    def execute_text(self, text):
        res = u""
        throw = False
        _LOG.debug("TEXT" + repr(text[:80]))
        for line in text.splitlines():
            try:
                _LOG.debug(_("Executing line: {0}").format(repr(line)))
                args = line.split(" ", 2)
                if len(args) == 3:
                    res += self.set_value(*args) + "\n"

                elif len(args) == 1:
                    if len(args[0].strip()) != 0:
                        for key, val in self.get_values(*args).items():
                            res += u"GET {0} = {1}\n".format(key, val)
            except ScriptError, e:
                res += e.traceback + "\n"
                throw = True

        if throw:
            raise ScriptError(_("Script did not execute properly"), res)
        return res

class SNMP2cProtocol(SNMPProtocol):
    """ SNMP v2c Protocol """

    def get_common_options(self):
        return "-v2c -c %(community)s %(host)s" % dict(
                community = self.community,
                host = self.host,
                )
