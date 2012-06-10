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

Provides a JSONRPCServer class for subclassing.

Example usage:
@TODO
"""

from twisted.web import resource
from twisted.web import server
from twisted.internet.defer import maybeDeferred
from twisted.python.failure import Failure

import jsonrpc

class JSONRPCServer(resource.Resource):
    """
    JSON-RPC server. You should subclass this, implement your own methods to be
    published and publish this as t.w.r.Resource.

    It will publish all methods that start with 'jsonrpc_'.
    """

    isLeaf = 1


    def render(self, request):
        """
        This is the 'main' RPC method. This will always be called when a request
        arrives and it's up to this method to dispatch it further.

        This method will call the appropriate 'exported' method (i.e. one
        starting with 'jsonrpc_) and it will pass the (async) result to
        self.cbResult.

        @type request: t.w.s.Request
        @param request: Request that arrived here

        @return Deferred that will eventually fire with the method's return
        values
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
            raise jsonrpc.JSONRPCError(
                    jsonrpc.METHOD_NOT_FOUND,
                    'Method %s not found' % request_dict['method'])

        return server.NOT_DONE_YET

    def cbResult(self, result, request, id_, version=jsonrpc.VERSION_1):
        """
        'callback with result'. Manages returning what the called function
        returned.

        @type result: mixed
        @param result: What the called function returned

        @type request: t.w.s.Request
        @param request: The request, that came from a client

        @type id_: int
        @param id_: id of the request

        @type version: float
        @param version: JSON-RPC version
        """

        print 'version:', type(version), version
        encoded = jsonrpc.encodeResponse(result, id_, version)

        request.write(encoded)
        request.finish()
