import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.trial.unittest import TestCase, SkipTest
from twisted.internet.defer import Deferred
from twisted.web.server import Site
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.internet.error import TimeoutError
from twisted.web.client import WebClientContextFactory
from twisted.internet import ssl
from twisted.cred.portal import Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.credentials import Anonymous, UsernamePassword
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory

from fastjsonrpc.client import ReceiverProtocol
from fastjsonrpc.client import StringProducer
from fastjsonrpc.client import Proxy
from fastjsonrpc import jsonrpc

from dummyserver import DummyServer, AuthDummyServer


class TestReceiverProtocol(TestCase):

    def setUp(self):
        self.rp = ReceiverProtocol(Deferred())

    def test_init(self):
        self.assertTrue(isinstance(self.rp.finished, Deferred))

    def test_dataReceivedOnce(self):
        data = 'some random string'

        self.rp.dataReceived(data)
        self.assertEquals(self.rp.body, data)

    def test_dataReceivedTwice(self):
        data1 = 'string1'
        data2 = 'string2'

        self.rp.dataReceived(data1)
        self.rp.dataReceived(data2)
        self.assertEquals(self.rp.body, data1 + data2)

    def test_connectionLostCalled(self):
        data = 'some random string'

        self.rp.dataReceived(data)
        self.rp.connectionLost(None)

        self.assertTrue(self.rp.finished.called)

    def test_connectionLostCalledData(self):
        data = 'some random string'
        self.rp.dataReceived(data)

        def called(data_received):
            self.assertEquals(data_received, data)

        self.rp.finished.addCallback(called)
        self.rp.connectionLost(None)
        return self.rp.finished


class DummyConsumer(object):

    def __init__(self):
        self.body = ''

    def write(self, data):
        self.body += data


class TestStringProducer(TestCase):

    def test_init(self):
        data = 'some random string'
        sp = StringProducer(data)

        self.assertEquals(sp.body, data)
        self.assertEquals(sp.length, len(data))

    def test_startProducing(self):
        data = 'some random string'
        sp = StringProducer(data)

        consumer = DummyConsumer()
        d = sp.startProducing(consumer)

        def finished(_):
            self.assertEquals(consumer.body, data)

        d.addCallback(finished)
        return d


class DummyResponse(object):

    def __init__(self, body):
        self.body = body

    def deliverBody(self, protocol):
        self.protocol = protocol
        self.protocol.dataReceived(self.body)
        self.protocol.connectionLost(None)


class TestProxy(TestCase):

    def setUp(self):
        site = Site(DummyServer())
        self.port = reactor.listenTCP(0, site)
        self.portNumber = self.port._realPortNumber

    def tearDown(self):
        self.port.stopListening()

    def test_init(self):
        url = 'http://example.org/abcdef'
        version = '2.0'

        proxy = Proxy(url, version)
        self.assertEquals(proxy.url, url)
        self.assertEquals(proxy.version, version)

    def test_init_agent(self):
        proxy = Proxy('', '')

        self.assertTrue(isinstance(proxy.agent, Agent))

    def test_bodyFromResponseProtocolBody(self):
        data = 'some random string'

        proxy = Proxy('', '')
        response = DummyResponse(data)
        d = proxy.bodyFromResponse(response)

        def finished(_):
            self.assertEquals(response.protocol.body, data)

        d.addCallback(finished)
        return d

    def test_bodyFromResponseDeferred(self):
        data = 'some random string'

        proxy = Proxy('', '')
        response = DummyResponse(data)
        d = proxy.bodyFromResponse(response)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_callRemoteV1Ok(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_callRemoteV2Ok(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_2)
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_callRemoteV1NoMethod(self):
        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('nosuchmethod')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Method nosuchmethod not found')
            self.assertEquals(result.errno, jsonrpc.METHOD_NOT_FOUND)
            self.assertEquals(result.version, jsonrpc.VERSION_1)

        e.addCallback(finished)
        return e

    def test_callRemoteV2InvalidParams(self):
        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_2)
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

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', data=data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_keywordsV2(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_2)
        d = proxy.callRemote('echo', data=data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_keywordsUnexpected(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', wrongname=data)
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            msg = 'jsonrpc_echo() got an unexpected keyword argument ' + \
                  '\'wrongname\''
            self.assertEquals(result.strerror, msg)
            self.assertEquals(result.errno, jsonrpc.INVALID_PARAMS)

        e.addCallback(finished)
        return d

    def test_timeout(self):
        """ Google doesn't offer any services on our crazy ports """
        addr = 'http://google.com:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1, connectTimeout=0.1)
        d = proxy.callRemote('sleep', 5)

        def finished(result):
            self.assertTrue(isinstance(result.value, TimeoutError))

        d.addErrback(finished)
        return d

    def test_anonymousLogin(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1, credentials=Anonymous())
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_loginNotNeccessary(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        credentials = UsernamePassword('user', 'password')
        proxy = Proxy(addr, credentials=credentials)
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d


class TestSSLProxy(TestCase):

    def setUp(self):
        if not (os.path.exists('../ssl-keys/server.key') and 
                os.path.exists('../ssl-keys/server.crt')):
            raise SkipTest('For testing SSL, please put server.key and ' + \
                           'server.crt to ssl-keys/')
        SSLFactory = ssl.DefaultOpenSSLContextFactory('../ssl-keys/server.key',
                                                      '../ssl-keys/server.crt')
        site = Site(DummyServer())
        self.port = reactor.listenSSL(0, site, contextFactory=SSLFactory)
        self.portNumber = self.port._realPortNumber

    def tearDown(self):
        self.port.stopListening()

    def test_init(self):
        url = 'https://example.org/abcdef'
        version = '2.0'

        proxy = Proxy(url, version, contextFactory=WebClientContextFactory())
        self.assertEquals(proxy.url, url)
        self.assertEquals(proxy.version, version)

    def test_init_agent(self):
        proxy = Proxy('', '', contextFactory=WebClientContextFactory())
        self.assertTrue(isinstance(proxy.agent, Agent))
        self.assertTrue(isinstance(proxy.agent._contextFactory,
                                   ssl.ClientContextFactory))

    def test_callRemote(self):
        """
        The test itself passes, but trial raises "Reactor was unclean" after
        tearDown.. Might be related to
        http://twistedmatrix.com/trac/ticket/5118
        """
        data = 'some random string'

        addr = 'https://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1,
                      contextFactory=WebClientContextFactory())
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

class TestHTTPAuth(TestCase):

    def setUp(self):
        checker = InMemoryUsernamePasswordDatabaseDontUse(user='password')
        portal = Portal(AuthDummyServer(), [checker])
        credentialFactory = BasicCredentialFactory('localhost')
        resource = HTTPAuthSessionWrapper(portal, [credentialFactory])
        site = Site(resource)

        self.port = reactor.listenTCP(0, site)
        self.portNumber = self.port._realPortNumber

    def tearDown(self):
        self.port.stopListening()

    def test_loginOk(self):
        data = 'some random string'

        addr = 'http://localhost:%s' % self.portNumber
        credentials = UsernamePassword('user', 'password')
        proxy = Proxy(addr, credentials=credentials)
        d = proxy.callRemote('echo', data)

        def finished(result):
            self.assertEquals(result, data)

        d.addCallback(finished)
        return d

    def test_loginWrongPassword(self):
        addr = 'http://localhost:%s' % self.portNumber
        credentials = UsernamePassword('user', 'wrong password')
        proxy = Proxy(addr, credentials=credentials)
        d = proxy.callRemote('echo', '')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Unauthorized')
            self.assertEquals(result.errno, jsonrpc.INVALID_REQUEST)

        e.addCallback(finished)
        return d

    def test_loginWrongUser(self):
        addr = 'http://localhost:%s' % self.portNumber
        credentials = UsernamePassword('wrong user', 'password1')
        proxy = Proxy(addr, credentials=credentials)
        d = proxy.callRemote('echo', '')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Unauthorized')
            self.assertEquals(result.errno, jsonrpc.INVALID_REQUEST)

        e.addCallback(finished)
        return d

    def test_noCredentials(self):
        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, jsonrpc.VERSION_1)
        d = proxy.callRemote('echo', '')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Unauthorized')
            self.assertEquals(result.errno, jsonrpc.INVALID_REQUEST)

        e.addCallback(finished)
        return d

    def test_anonymousError(self):
        addr = 'http://localhost:%s' % self.portNumber
        proxy = Proxy(addr, credentials=Anonymous())
        d = proxy.callRemote('echo', '')
        e = self.assertFailure(d, jsonrpc.JSONRPCError)

        def finished(result):
            self.assertEquals(result.strerror, 'Unauthorized')
            self.assertEquals(result.errno, jsonrpc.INVALID_REQUEST)

        e.addCallback(finished)
        return d
