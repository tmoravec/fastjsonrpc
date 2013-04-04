import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import re

from dummynetstringserver import DummyProtocol

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.protocol import Factory


class NetstringDecoder(object):

    def __init__(self, netstring):
        self.netstring = netstring
        self.supposedLength, self.string = self.parse(netstring)


    def parse(self, netstring):
        pattern = r'(\d+):(.*),'
        match = re.match(pattern, netstring)
        return match.group(1), match.group(2)


class TestServer(unittest.TestCase):
    timeout = 1

    def setUp(self):
        factory = Factory()
        factory.protocol = DummyProtocol
        self.proto = factory.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()
        self.proto.makeConnection(self.tr)

    def _callMethod(self, string):
        netstring = str(len(string)) + ':' + string + ','
        self.proto.dataReceived(netstring)
        decoder = NetstringDecoder(self.tr.value())
        return decoder.string

    def _testResult(self, request, expected):
        result = self._callMethod(request)
        self.assertEquals(expected, result)

    def test_emptyRequest(self):
        request = ''
        expected = '{"jsonrpc": "2.0", "id": null, "error": ' + \
                   '{"message": "Parse error", "code": -32700}}'

        self._testResult(request, expected)

    def test_malformed(self):
        request = '{"method": "sql", "id'
        expected = '{"jsonrpc": "2.0", "id": null, "error": ' + \
                   '{"message": "Parse error", "code": -32700}}'
        self._testResult(request, expected)

    def test_caseSensitiveMethodV1(self):
        request = '{"method": "ECHO", "id": "ABCD", "params": ["AB"]}'
        expected = '{"result": null, "id": "ABCD", "error": {' + \
                   '"message": "Method ECHO not found", "code": -32601}}'
        self._testResult(request, expected)
