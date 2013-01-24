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
JSONRPC Client
==============

Provides a Proxy class, that can be used for calling remote functions via
JSON-RPC.
"""

from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

import jsonrpc


class ReceiverProtocol(Protocol):
    """
    Protocol for receiving the server response. It's only purpose is to get the
    HTTP request body. Instance of this will be passed to the Response's
    deliverBody method.
    """
    def __init__(self, finished):
        """
        @type finished: t.i.d.Deferred
        @param finished: Deferred to be called when we've got all the data.
        """

        self.body = ''
        self.finished = finished

    def dataReceived(self, data):
        """
        Appends data to the internal buffer.

        @type data: str (bytearray, buffer?)
        @param data: Data from server. 'Should' be (a part of) JSON
        """

        self.body += data

    def connectionLost(self, reason):
        """
        Fires the finished's callback with data we've received.

        @type reason: t.p.f.Failure
        @param reason: Failure, wrapping several potential reasons. It can
        wrap t.w.c.ResponseDone, in which case everything is OK. It can wrap
        t.w.h.PotentialDataLoss. Or it can wrap an Exception, in case of an
        error.

        @TODO inspect reason for failures
        """

        self.finished.callback(self.body)


class StringProducer(object):
    """
    There's no FileBodyProducer in Twisted < 12.0.0
    See http://twistedmatrix.com/documents/current/web/howto/client.html for
    details about this class
    """
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class Proxy(object):
    """
    A proxy to one specific JSON-RPC server. Pass the server URL to the
    constructor and call proxy.callRemote('method', *args) to call 'method'
    with *args.
    """

    def __init__(self, url, version=jsonrpc.VERSION_1):
        """
        @type url: str
        @param url: URL of the RPC server. Only supports HTTP for now, HTTPS
        (and more) might come in the future.
        @TODO more detailed description of url

        @type version: int
        @param version: Which JSON-RPC version to use? The default is 1.0.
        """

        self.url = url
        self.version = version

    def bodyFromResponse(self, response):
        """
        Parses out the body from the response

        @type response: t.w.c.Response
        @param response: Response object from the call

        @rtype: t.i.d.Deferred
        @return: Deferred, that will fire callback with body of the response
            (as string)
        """

        finished = Deferred()
        response.deliverBody(ReceiverProtocol(finished))
        return finished

    def callRemote(self, method, *args, **kwargs):
        """
        Remotely calls the method, with args. Given that we keep reference to
        the call via the Deferred, there's no need for id. It will coin some
        random anyway, just to satisfy the spec.

        @type method: str
        @param method: Method name

        @type *args: list
        @param *args: List of agruments for the method.

        @rtype: t.i.d.Deferred
        @return: Deferred, that will fire with whatever the 'method' returned.
        @TODO support batch requests
        """

        if kwargs:
            json_request = jsonrpc.encodeRequest(method, kwargs,
                                                 version=self.version)
        else:
            json_request = jsonrpc.encodeRequest(method, args,
                                                 version=self.version)

        agent = Agent(reactor)
        body = StringProducer(json_request)
        headers = Headers({'Content-Type': ['application/json'],
                           'Content-Length': [str(body.length)]})

        d = agent.request('POST', self.url, headers, body)
        d.addCallback(self.bodyFromResponse)
        d.addCallback(jsonrpc.decodeResponse)
        return d
