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

#!/usr/bin/python
import sys
import getpass

"""
Interactive console emulator.

Presents the caller with a MOTD, Username and password prompt and expects
the password to match the username.

It then provides a console prompt-like behavior.
- ROOT_CMD allows becoming root by entering the password
- UNROOT_CMD allows leaving root session
- EXIT_CMD leaves
- everything else is outputted if it contains echo, or ignored
"""

PROMPT = "fake> "
RPROMPT = "fake# "
USERNAME = "Username :"
PASSWD = "Password :"
MOTD = "Welcome to this fake prompt!"
ROOT_CMD = "enable"
UNROOT_CMD = "disable"
EXIT_CMD = "exit"

def main():
    print MOTD
    username = raw_input(USERNAME)
    password = getpass.getpass(PASSWD)
    if username != password:
        print "Failed."
        sys.exit(1)

    root = False
    while True:
        try:
            if root:
                line = raw_input(RPROMPT)
            else:
                line = raw_input(PROMPT)
        except Exception:
            sys.exit(0)

        if line == ROOT_CMD:
            if root:
                print "Already Root!"
            else:
                root_pass = getpass.getpass(PASSWD)
                if password == root_pass:
                    root = True
                else:
                    print "Bad password!"

        elif line == UNROOT_CMD:
            if not root:
                print "Not root!"
            else:
                root = False
        elif line == EXIT_CMD:
            print "Bye bye"
            sys.exit(0)
        else:
            if "echo" in line:
                print line





if __name__ == '__main__':
    main()
