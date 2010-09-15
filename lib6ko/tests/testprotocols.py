import sys, os
import unittest

from operator import attrgetter

from lib6ko.protocol import *
from lib6ko.run import ProtocolChain

from lib6ko.tests.mocks.protocols import createProtocolDescriptor

class Test_ScopedDict(unittest.TestCase):
    def test_kw_create(self):
        s = ScopedDict(
            key1="val1",
            key2="val2",
        )
        self.assertEquals(
            sorted(s.items()),
            [
                ("key1", "val1"),
                ("key2", "val2"),
            ],
            )

    def test_tuple_create(self):
        s = ScopedDict(
            (
                ("key1", "val1"),
                ("key2", "val2"),
            ),
            )
        self.assertEquals(
            sorted(s.items()),
            [
                ("key1", "val1"),
                ("key2", "val2"),
            ],
            )

    def test_nesting(self):
        s = ScopedDict(
            key=type(
                "obj",
                (object, ),
                {"attribute1": "value1"},
                )(),
            d={
                "key":"val2",
                "key::key":"val::val",
                },
            )
        s["self"] = s

        # Scope on sub-dict: key
        self.assertEquals(
            getattr(s, "d::key"),
            "val2",
            )

        # Scope on sub-object
        self.assertEquals(
            getattr(s, "key::attribute1"),
            "value1",
            )

        # Scope activates in items if they are scopeddict's too
        self.assertEquals(
            getattr(s, "self::key::attribute1"),
            "value1",
            )

        # In subdict, scope will do a key lookup
        self.assertEquals(
            getattr(s, "d::key::key"),
            "val::val",
            )

        # A key should not be returned in the scoped dict
        self.assertRaises(
            AttributeError,
            getattr,
                s, "obj",
            )

        self.assertRaises(
            AttributeError,
            getattr,
                s, "self::obj",
            )

class Test_ProtocolOptions(unittest.TestCase):
    def setUp(self):
        self.params = ScopedDict(
            param=dict(
                param1="value1",
                param2=2,
                ),
            ap=dict(
                ipv4Address="0.0.0.0",
                ),
            )
        self.proto = Protocol(self.params)

    def test_require(self):
        self.assertEquals(
            self.proto.require("ap::ipv4Address"),
            self.params["ap"]["ipv4Address"],
            )
        self.assertRaises(
            MissingParametersException,
            self.proto.require,
            "somethingelse",
            )
        self.assertEquals(
            self.proto.require("somethingelse", "default"),
            "default",
            )

    def test_require_param(self):
        self.assertEquals(
            self.proto.require_param("param1"),
            "value1",
            )
        self.assertEquals(
            self.proto.require_param("param2"),
            2,
            )
        self.assertRaises(
            MissingParametersException,
            self.proto.require_param,
            "param3",
            )
        self.assertEquals(
            self.proto.require_param("param3", "default"),
            "default",
            )

class TestProtocolChain(unittest.TestCase):
    def test_ctor(self):
        self.assertRaises(TypeError,
            ProtocolChain,
            None,
            {},
            )

    def test_empty_chain(self):
        chain = ProtocolChain([], {})
        self.assertRaises(
            ScriptError,
            attrgetter("protocol"),
            chain,
            )

        #Should do nothing, and not fail
        del chain.protocol
        
    def test_failover(self):
        proto1 = createProtocolDescriptor("Proto1",
            failure=TemporaryFailure(""),
            )
        proto3 = createProtocolDescriptor("Proto3",
            failure=PermanentFailure(""),
            )
        proto4 = createProtocolDescriptor("Proto4",
            failure=Exception(""),
            )
        proto2 = createProtocolDescriptor("Proto2")
        chain = ProtocolChain([proto1], {})

        #Without failover, it should fail
        self.assertRaises(
            ScriptError,
            attrgetter("protocol"),
            chain,
            )

        chain = ProtocolChain([proto1, proto3, proto4, proto2], {})
        self.assertTrue(
            isinstance(chain.protocol, proto2.get_class()),
            )
            
    def test_singlelike(self):
        proto1 = createProtocolDescriptor("Proto1", {"a":"a"})
        chain = ProtocolChain([proto1], {})
        proto = chain.protocol
        self.assertEquals(proto, chain.protocol)

    def test_delproto(self):
        proto1 = createProtocolDescriptor("Proto1", {"a":"a"})
        chain = ProtocolChain([proto1], {})
        #Before aquiring, delete does nothing
        del chain.protocol

        #Aquire
        proto = chain.protocol
        #Now we delete
        del chain.protocol
        #Last protocol, can't work now
        self.assertRaises(
            ScriptError,
            attrgetter("protocol"),
            chain,
            )
        #Del again should do nothing
        del chain.protocol
        
if __name__ == '__main__':
    unittest.main()
