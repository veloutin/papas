from abc import ABCMeta, abstractmethod
from operator import attrgetter

import urllib2


def parse_target(target_uri):
    return urllib2.urlparse.urlparse(target_uri)

class ConfigurationException(Exception):
    """ Thrown when not enough configuration is passed to a Transport """

class TransportException(Exception):
    """ Base class for Transport Exceptions """

class ConnectionLost(TransportException):
    """ Exception for dropped connection """

class ConnectedTransport(object):
    """
    ConnectedTransport represents transport protocols that must have a
    connection established before allowing execution of commands.
    """
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def connect(self):
        """ connect to the remote host """

    @abstractmethod
    def disconnect(self):
        """ disconnect """

class InteractiveTransport(object):
    """
    InteractiveTransport is a protocol that allows interactive execution of
    commands with write/read.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, text):
        """ send text to the remote host """

    def write_line(self, text, lf="\n"):
        """ write a line with an appended newline """
        self.write(text + lf)

    @abstractmethod
    def read(self, count=None):
        """ read text from the remote host """


class CommandTransport(object):
    """
    CommandTransport is a protocol that allows executing commands directly 
    without requiring a shell
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self, command):
        """ execute a command on the remote host """


class BaseTransport(object):
    """ Base transport class """

    def __init__(self, parameters, architecture):
        self.params = parameters
        self.arch = architecture

    def require(self, name, default=None):
        try:
            return self.params.get(name, default=default)
        except (KeyError, AttributeError):
            raise ConfigurationException("{0} is a required parameter".format(name))
            
    def require_param(self, name, default=None):
        return self.require("param::" + name, default)

