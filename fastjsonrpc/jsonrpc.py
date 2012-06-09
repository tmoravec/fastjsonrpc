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
"""

try:
    import cjson as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            import simplejson as json
        except ImportError:
            raise ImportError('cjon, json or simplejson required')

import random

from zope.interface import implements

from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer

VERSION_1 = 1.0
VERSION_2 = 2.0

ID_MIN = 1
ID_MAX = 2**31 - 1  # 32-bit maxint

def getJSONRequest(method, args, id_=0, version=VERSION_1):
    """
    Returns a JSON object representation of the request.

    @type id_: int or None
    @param id_: request ID. If None, a notification will be sent. If 0 (the
    default), we'll coin some random.

    @type method: str
    @param method: Method name

    @type args: list
    @param args: List of arguments for the method

    @type version: float
    @param version: Which JSON-RPC version to use? Defaults to 1.0

    @return string JSON representation of the request
    """

    request = {}
    request['method'] = method
    request['params'] = args

    if id_ is not None:
        if id_ == 0:
            id_ = random.randint(ID_MIN, ID_MAX)
        request['id'] = id_

    if version == VERSION_2:
        request['jsonrpc'] = '2.0'

    return json.dumps(request)

def getReturnFromJSON(json_response):
    """
    Parses response JSON and returns what the server responded.

    @type json_response: str
    @param json_response: JSON from the server

    @TODO handle exceptions. Create a custom exception for this?
    """

    response = json.loads(json_response)

    if 'result' in response and response['result'] is not None:
        return response['result']

    if 'error' in response and response['error'] is not None:
        raise Exception(response['error'])

    raise ValueError('Not a valid JSON-RPC response')

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
