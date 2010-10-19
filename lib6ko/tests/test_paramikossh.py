import unittest
from lib6ko.architectures.paramiko_ssh import (
    ParamikoConsole,
    InteractiveWrapper,
    InteractiveParamikoConsole,
    )

class Test_ParamikoSSH(unittest.TestCase):
    def test_create_dumb(self):
        p = ParamikoConsole()
        ip = InteractiveParamikoConsole()
        i = InteractiveWrapper(None, None)

if __name__ == '__main__':
    unittest.main()
