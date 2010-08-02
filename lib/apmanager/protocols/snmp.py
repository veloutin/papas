
from ..protocol import SNMPProtocol

class SNMP2cProtocol(SNMPProtocol):
    """ SNMP v2c Protocol """

    def get_common_options(self):
        return "-v2c -c adm-99-712rw 10.145.45.99"
