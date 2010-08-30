
from ..protocol import SNMPProtocol

class SNMP2cProtocol(SNMPProtocol):
    """ SNMP v2c Protocol """

    def get_common_options(self):
        return "-v2c -c %(community)s %(host)s" % dict(
                community = self._community,
                host = self._host,
                )
