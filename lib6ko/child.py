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

    def sendline(self, line):
        self.send(line + "\n")

    def read(self):
        return self._child.stdout.read()

