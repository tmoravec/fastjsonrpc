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
from twisted.internet.defer import DeferredList
from twisted.internet.defer import succeed

import jsonrpc

class JSONRPCServer(resource.Resource):
    """
    JSON-RPC server. Subclass this, implement your own methods and publish
    this as t.w.r.Resource using t.w.s.Site.

    It will expose all methods that start with 'jsonrpc_' (without the
    'jsonrpc_' part).

    @TODO Think twice what belongs to jsonrpc and what belongs here.
    """

    isLeaf = 1

    def _getRequestContent(self, request):
        """
        Parse the JSON from the request.

        @type request: t.w.s.Request
        @param request: The request from client

        @rtype: list
        @return: List of dicts, one dict per method call.

        @raise JSONRPCError: If there's error in parsing.
        """

        request.content.seek(0, 0)
        request_content = request.content.read()
        request_json = jsonrpc.decodeRequest(request_content)

        if not isinstance(request_json, list):
            request_json = [request_json]

        return request_json

    def _parseError(self, request):
        """
        Coin a 'parse error' response and finish the request

        @type request: t.w.s.Request
        @param request: Request from client
        """

        response = jsonrpc.parseError()
        self._sendResponse(response, request)

    def _callMethod(self, request_dict):
        """
        Here we actually call the method. Although we don't return anything,
        reactor will take care of the deferred.

        @type request_dict: dict
        @param request_dict: Dict with details about the request

        @type request: t.w.s.Request
        @param request: The request from client

        @raise JSONRPCError: When method not found.
        """

        function = getattr(self, 'jsonrpc_%s' % request_dict['method'], None)
        if callable(function):

            if 'params' in request_dict:
                if isinstance(request_dict['params'], dict):
                    d = maybeDeferred(function, **request_dict['params'])
                else:
                    d = maybeDeferred(function, *request_dict['params'])
            else:
                d = maybeDeferred(function)

            return d

        else:
            self._methodNotFound(request_dict)

    def render(self, request):
        """
        This is the 'main' RPC method. This will always be called when a request
        arrives and it's up to this method to dispatch it further.

        This method will call the appropriate exposed method (i.e. one
        starting with 'jsonrpc_) and it will pass the (async) result to
        self._cbResult.

        @type request: t.w.s.Request
        @param request: Request from client

        @rtype: some constant :-)
        @return: NOT_DONE_YET signalizing, that there's Deferred, that will take
        care about sending the response.
        """

        try:
            request_content = self._getRequestContent(request)
        except jsonrpc.JSONRPCError as e:
            self._parseError(request)
            return server.NOT_DONE_YET

        dl = []
        for request_dict in request_content:
            try:
                jsonrpc.verifyMethodCall(request_dict)
                d = self._callMethod(request_dict)
                d.addBoth(jsonrpc.prepareMethodResponse, request_dict['id'],
                          request_dict['jsonrpc'])
            except jsonrpc.JSONRPCError as e:
                method_response = jsonrpc.prepareMethodResponse(
                        e, request_dict['id'], request_dict['jsonrpc'])
                d = succeed(method_response)
            finally:
                dl.append(d)

        dl = DeferredList(dl, consumeErrors=True)
        dl.addBoth(self._cbFinishRequest, request)

        return server.NOT_DONE_YET

    def _cbFinishRequest(self, results, request):
        """
        Manages sending the response to the client and finishing the request.
        This gets called after all methods have returned.

        @type results: list
        @param results: List of tuples (success, result) what DeferredList
            returned.

        @type request: t.w.s.Request
        @param request: The request that came from a client

        @type id_: int
        @param id_: id of the request

        @type version: float
        @param version: JSON-RPC version
        """

        method_responses = []
        for (success, result) in results:
            if result is not None:
                method_responses.append(result)

        if len(method_responses) == 1:
            method_responses = method_responses[0]

        response = jsonrpc.prepareCallResponse(method_responses)
        self._sendResponse(response, request)

    def _sendResponse(self, response, request):
        """
        Send the response back to client. Expects it to be already serialized
        into JSON.

        @type response: str
        @param response: JSON with the response

        @type request: t.w.s.Request
        @param request The request that came from a client
        """

        if response != '[]':
            request.setHeader('Content-Type', 'application/json')
            request.setHeader('Content-Length', len(response))
            request.write(response)

        request.finish()

