import re

import commands
import logging

class Protocol(object):
    """ Base Protocol Object """

class ConsoleProtocol(Protocol):
    """ Console Protocol """


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


