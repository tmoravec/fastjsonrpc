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
from twisted.python.failure import Failure

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

    def _methodNotFound(self, request_dict):
        """
        Raise JSONRPCError with all info we can get from the request

        @type request_dict: dict
        @param request_dict: Parsed request from client

        @exception jsonrpc.JSONRPCError
        @TODO refactor with _methodResponse
        """

        msg = 'Method %s not found' % request_dict['method']

        if 'id' in request_dict:
            id_ = request_dict['id']
        else:
            id_ = None

        if 'jsonrpc' in request_dict:
            version = request_dict['jsonrpc']
        else:
            version = None

        return jsonrpc.JSONRPCError(msg, jsonrpc.METHOD_NOT_FOUND, id_=id_,
                                    version=version)

    def _getRequestContent(self, request):
        """
        Parse the JSON from the request. Return it as a dict.

        @type request: t.w.s.Request
        @param request: The request from client

        @rtype: dict
        @return: dict, containing id, method, params and (if present) jsonrpc

        @raise JSONRPCError: If there's error in parsing.
        """

        request.content.seek(0, 0)
        request_content = request.content.read()
        request_dict = jsonrpc.decodeRequest(request_content)

        return request_dict

    def _callMethod(self, request_dict):
        """
        Here we actually call the method. Although we don't return anything,
        reactor will take care of the deferred.

        @type request_dict: dict
        @param request_dict: Dict with details about the request

        @type request: t.w.s.Request
        @param request: The request from client
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
            e = self._methodNotFound(request_dict)
            raise e

    def _methodResponse(self, result, request_dict):
        """
        Add all available info to the result - i.e. prepare the response for a
        single method

        @type result: mixed
        @param result: What the called function returned

        @type request_dict: dict
        @param request_dict: Dict with info about the called method

        @rtype: dict
        @return: Method result with all info we should add, ready to be
            serialized.
        """

        if request_dict['id'] is None:
            # Notification.. Don't return anything
            return None

        if isinstance(result, Failure):
            result = result.value

        if 'jsonrpc' in request_dict:
            version = request_dict['jsonrpc']
        else:
            version = jsonrpc.VERSION_1

        return jsonrpc.prepareResponse(result, request_dict['id'], version)

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
            # failed to parse the request
            # TODO respond with PARSE_ERROR
            request.finish()
            return server.NOT_DONE_YET

        if not isinstance(request_content, list):
            request_content = [request_content]

        dl = []
        for request_dict in request_content:
            try:
                jsonrpc.verifyMethodCall(request_dict)
                d = self._callMethod(request_dict)
                d.addBoth(self._methodResponse, request_dict)
            except jsonrpc.JSONRPCError as e:
                d = succeed(self._methodResponse(e, request_dict))
            finally:
                dl.append(d)

        dl = DeferredList(dl, consumeErrors=True)
        dl.addBoth(self._finishRequest, request)

        return server.NOT_DONE_YET

    def _finishRequest(self, results, request):
        """
        Manages sending the response to the client and finishing the request.
        This gets called after all methods have returned.

        @type results: list
        @param results: List of tuples (success, result) as DeferredList
            returns.

        @type request: t.w.s.Request
        @param request: The request that came from a client

        @type id_: int
        @param id_: id of the request

        @type version: float
        @param version: JSON-RPC version
        """

        ret = []
        for (success, result) in results:
            if result is not None:
                ret.append(result)

        if len(ret) == 1:
            ret = ret[0]

        if ret != []:
            self._sendResponse(jsonrpc.jdumps(ret), request)

        request.finish()

    def _sendResponse(self, response, request):
        """
        Send the response back to client. Expects it to be already serialized
        into JSON.

        @type response: str
        @param response: JSON with the response

        @type request: t.w.s.Request
        @param request The request that came from a client
        """

        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Content-Length', len(response))
        request.write(response)

