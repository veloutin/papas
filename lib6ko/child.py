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

"""
This module is intended to provide a simple interface for child processes,
without having to know what the implementation is.
"""
import subprocess
import fcntl
import os

def set_blocking(fileobj, block=True):
    fd = fileobj.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    if block:
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
    else:
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        

class Child(object):
    def __init__(self, command):
        #Open a subprocess
        self._child = subprocess.Popen(command,
            bufsize=0,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            universal_newlines=True,
            )

        set_blocking(self._child.stdout, False)
    
    def send(self, data):
        self._child.stdin.write(data)

    def send_line(self, line):
        self.send(line + "\n")

    def read(self, max_bytes=-1):
        try:
            return self._child.stdout.read(max_bytes)
        except IOError as e:
            if e.errno == 11:
                #Resouce temporarily unavailable -> no data to read
                return ""
            else:
                raise

    def get_echo(self):
        try:
            return bool(termios.tcgetattr(self._child.stdin.fileno())[3] & termios.ECHO)
        except Exception:
            return None

