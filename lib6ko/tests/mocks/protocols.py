from lib6ko.protocol import (
    Protocol,
    )


def createProtocolDescriptor(
        name,
        params={},
        failure=None,
        base_protocol_class=Protocol,
    ):
    """
    Protocol Descriptor Factory

    Returns classes that mimics the behavior of the
    apmanager.accesspoints.architecture.Protocol and provides:
     - load_default_parameter_values()
     - get_class()
    
    Parameters:
     - name : class name
     - params : dictionary of required parameters, where the key is the name
           and the value is the default_value
     - failure : allows forcing the protocol to launch an exception on init.
           If provided and not None, the provided value will be raised.  
    """

    class MockProtocol(base_protocol_class):
        def __init__(self, parameters):
            if failure:
                raise failure
            super(MockProtocol, self).__init__(parameters)
            for key, val in params.items():
                self.require_param(key, val)

    class _WrapperBase(object):
        def load_default_parameter_values(self):
            return dict(
                filter(
                    lambda s: s[1] is not None,
                    params.items(),
                    )
                )

        def get_class(self):
            return MockProtocol

    return type(
        #Class name
        name,
        #Bases
        (_WrapperBase, ),
        #Attributes
        {},
        )()
                

