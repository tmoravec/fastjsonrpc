import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.trial import unittest
from twisted.internet.protocol import Factory
from twisted.internet import reactor

from fastjsonrpc.netstringclient import Proxy
from fastjsonrpc import jsonrpc
from dummynetstringserver import DummyProtocol

class TestProxy(unittest.TestCase):
    """ @TODO refactor with test_client """

    def setUp(self):
        factory = Factory()
        factory.protocol = DummyProtocol
        self.port = reactor.listenTCP(0, factory)
        self.addr = 'localhost:%s' % self.port._realPortNumber

    def tearDown(self):
        self.port.stopListening()

    def test_init(self):
        hostname = 'example.com'
        port = 8111
        url = '%s:%s' % (hostname, port)
        version = '2.0'
        timeout = 40
        verbose = True

        proxy = Proxy(url, version, timeout, verbose)
        self.assertEquals(proxy.hostname, hostname)
        self.assertEquals(proxy.port, port)
        self.assertEquals(proxy.version, version)
        self.assertEquals(proxy.timeout, timeout)
        self.assertEquals(proxy.verbose, verbose)

    def test_callRemoteV1Ok(self):
        string = 'some rubbish'

        proxy = Proxy(self.addr)
        d = proxy.callRemote('echo', string)
        d.addCallback(self.assertEquals, string)
        return d

    def test_callRemoteV2Ok(self):
        string = 'some rubbish'

        proxy = Proxy(self.addr, '2.0')
        d = proxy.callRemote('echo', string)
        d.addCallback(self.assertEquals, string)
        return d

    def test_callRemoteNoMethod(self):
        proxy = Proxy(self.addr)
        d = proxy.callRemote('nosuchmethod')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Method nosuchmethod not found')
            self.assertEquals(result.errno, jsonrpc.METHOD_NOT_FOUND)
            self.assertEquals(result.version, jsonrpc.VERSION_1)

        e.addCallback(finished)
        return e

    def test_callRemoteV2InvalidParams(self):
        proxy = Proxy(self.addr, jsonrpc.VERSION_2)
        d = proxy.callRemote('echo', 'abc', 'def')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            msg = 'jsonrpc_echo() takes exactly 2 arguments (3 given)'
            self.assertEquals(result.strerror, msg)
            self.assertEquals(result.errno, jsonrpc.INVALID_PARAMS)
            self.assertEquals(result.version, unicode(jsonrpc.VERSION_2))

        e.addCallback(finished)
        return e

    def test_keywordsV1(self):
        data = 'some random string'

        proxy = Proxy(self.addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', data=data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_keywordsUnexpected(self):
        data = 'some random string'

        proxy = Proxy(self.addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', wrongname=data)
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            msg = 'jsonrpc_echo() got an unexpected keyword argument ' + \
                  '\'wrongname\''
            self.assertEquals(result.strerror, msg)
            self.assertEquals(result.errno, jsonrpc.INVALID_PARAMS)

        e.addCallback(finished)
        return d
