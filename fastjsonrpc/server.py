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

from twisted.web import resource
from twisted.web import server
from twisted.internet.defer import maybeDeferred
from twisted.python.failure import Failure

import jsonrpc

class JSONRPCServer(resource.Resource):
    """
    JSON-RPC server. Subclass this, implement your own methods and publish
    this as t.w.r.Resource using t.w.s.Site.

    It will expose all methods that start with 'jsonrpc_' (without the
    'jsonrpc_' part).
    """

    isLeaf = 1


    def render(self, request):
        """
        This is the 'main' RPC method. This will always be called when a request
        arrives and it's up to this method to dispatch it further.

        This method will call the appropriate exposed method (i.e. one
        starting with 'jsonrpc_) and it will pass the (async) result to
        self.cbResult.

        @type request: t.w.s.Request
        @param request: Request from client

        @rtype: some constant :-)
        @return: NOT_DONE_YET signalizing, that there's Deferred, that will take
        care about sending the response.

        @TODO Support for **kwargs
        """

        request.content.seek(0, 0)
        request_content = request.content.read()
        request_dict = jsonrpc.decodeRequest(request_content)

        function = getattr(self, 'jsonrpc_%s' % request_dict['method'], None)
        if callable(function):

            # Here we actually call the function!
            d = maybeDeferred(function, *request_dict['params'])
            d.addBoth(self.cbResult, request, request_dict['id'],
                      request_dict['jsonrpc'])

        else:

            # Send the error right now, before returning from this function.
            # The server doesn't care what happens first.
            exception = jsonrpc.JSONRPCError(
                    'Method %s not found' % request_dict['method'],
                    jsonrpc.METHOD_NOT_FOUND)
            f = Failure(exception)
            self.cbResult(f, request, request_dict['id'],
                          request_dict['jsonrpc'])


        return server.NOT_DONE_YET

    def cbResult(self, result, request, id_, version=jsonrpc.VERSION_1):
        """
        'callback with result'. Manages returning the methods return value(s).

        @type result: mixed
        @param result: What the called function returned

        @type request: t.w.s.Request
        @param request: The request that came from a client

        @type id_: int
        @param id_: id of the request

        @type version: float
        @param version: JSON-RPC version
        """

        encoded = jsonrpc.encodeResponse(result, id_, version)

        request.setHeader('Content-Type', 'text/json')
        request.setHeader('Content-Length', len(encoded))
        request.write(encoded)
        request.finish()
