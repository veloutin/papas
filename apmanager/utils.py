# -*- coding: utf-8 -*-
#
# $Revision: 1.64 $
# $Date: 2005/09/26 19:58:43 $
# $Author: dwelch $
#
# (c) Copyright 2001-2005 Hewlett-Packard Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

from __future__ import generators

# Std Lib
import sys, os, fnmatch, tempfile, socket, struct, select, time
import fcntl, errno, stat, string, xml.parsers.expat, commands

# Local
#from g import *
#from codes import *


# For pidfile locking (must be "static" and global to the whole app)
prv_pidfile = None
prv_pidfile_name = ""


def get_pidfile_lock ( a_pidfile_name="" ):
    """ Call this to either lock the pidfile, or to update it after a fork()
        Credit: Henrique M. Holschuh <hmh@debian.org>
    """
    global prv_pidfile
    global prv_pidfile_name
    if prv_pidfile_name == "":
        try:
            prv_pidfile_name = a_pidfile_name
            prv_pidfile = os.fdopen(os.open(prv_pidfile_name, os.O_RDWR | os.O_CREAT, 0644), 'r+')
            fcntl.fcntl(prv_pidfile.fileno(), fcntl.F_SETFD, fcntl.FD_CLOEXEC)
            while 1:
                try:
                    fcntl.flock(prv_pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (OSError, IOError), e:
                    if e.errno == errno.EINTR:
                        continue
                    elif e.errno == errno.EWOULDBLOCK:
                        try:
                            prv_pidfile.seek(0)
                            otherpid = int(prv_pidfile.readline(), 10)
                            sys.stderr.write ("can't lock %s, running daemon's pid may be %d\n" % (prv_pidfile_name, otherpid))
                        except (OSError, IOError), e:
                            sys.stderr.write ("error reading pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))

                        sys.exit(1)
                    sys.stderr.write ("can't lock %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))
                    sys.exit(1)
                break
        except (OSError, IOError), e:
            sys.stderr.write ("can't open pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))
            sys.exit(1)
    try:
        prv_pidfile.seek(0)
        prv_pidfile.write("%d\n" % (os.getpid()))
        prv_pidfile.flush()
        prv_pidfile.truncate()
    except (OSError, IOError), e:
        log.error("can't update pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))



def daemonize ( stdin='/dev/null', stdout='/dev/null', stderr='/dev/null' ):
    """
    Credit: Jürgen Hermann, Andy Gimblett, and Noah Spurrier
            http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012

    Proper pidfile support: Henrique M. Holschuh <hmh@debian.org>
    """
    # Try to lock pidfile if not locked already
    if prv_pidfile_name != '' or prv_pidfile_name != "":
        get_pidfile_lock( prv_pidfile_name )

    # Do first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit first parent.
    except OSError, e:
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror)    )
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()

    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit second parent.
    except OSError, e:
        sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror)    )
        sys.exit(1)

    if prv_pidfile_name != "":
        get_pidfile_lock()

    # Now I am a daemon!

    # Redirect standard file descriptors.
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

