"""
Copyright 2012 Tadeas Moravec

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


==============
JSONRPC Server
==============

Provides JSONRPCServer class, which can be used to expose methods via RPC.
"""

from twisted.protocols import basic
#from twisted.python import log
from twisted.internet.protocol import Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.defer import Deferred

import jsonrpc


class JSONRPCProtocol(basic.NetstringReceiver):

    def stringReceived(self, string):
        """
        """
        self.factory.responseReceived(string)
        self.transport.loseConnection()


class JSONRPCClientFactory(Factory):

    def __init__(self, json_string, proxy):

        self.json_string = json_string
        self.response = None
        self.proxy = proxy

    def buildProtocol(self, addr):

        p = JSONRPCProtocol()
        p.factory = self
        return p

    def responseReceived(self, json_response):

        self.proxy.responseReceived(json_response)


class Proxy(object):

    def __init__(self, url, version=jsonrpc.VERSION_1, timeout=30,
                 verbose=False):

        self.hostname, self.port = url.split(':')
        self.port = int(self.port)
        self.version = version
        self.timeout = timeout
        self.verbose = verbose

    def gotProtocol(self, p, json_request):

        p.sendString(json_request)

    def responseReceived(self, json_response):

        self.response_deferred.callback(json_response)

    def callRemote(self, method, *args, **kwargs):

        if kwargs:
            json_request = jsonrpc.encodeRequest(method, kwargs,
                                                 version=self.version)
        else:
            json_request = jsonrpc.encodeRequest(method, args,
                                                 version=self.version)

        if self.verbose:
            print ('Sending: %s' % json_request)

        self.factory = JSONRPCClientFactory(json_request, self)
        point = TCP4ClientEndpoint(reactor, self.hostname, self.port,
                                   timeout=self.timeout)
        d = point.connect(self.factory)
        d.addCallback(self.gotProtocol, json_request)

        self.response_deferred = Deferred()
        return self.response_deferred
