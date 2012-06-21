import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import re

from fastjsonrpc import jsonrpc
from twisted.trial.unittest import TestCase

class TestEncodeRequest(TestCase):

    def test_noArgs(self):
        self.assertRaises(TypeError, jsonrpc.encodeRequest)

    def test_onlyMethod(self):
        result = jsonrpc.encodeRequest('method')
        pattern = '\{"method": "method", "id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodIdInt(self):
        result = jsonrpc.encodeRequest('method', id_=123)
        expected = '{"method": "method", "id": 123}'
        self.assertEquals(result, expected)

    def test_methodIdStr(self):
        result = jsonrpc.encodeRequest('method', id_='abc')
        expected = '{"method": "method", "id": "abc"}'
        self.assertEquals(result, expected)

    def test_methodArgs(self):
        result = jsonrpc.encodeRequest('method', ['abc', 'def'])
        pattern = '\{"params": \["abc", "def"\], "method": "method", '
        pattern += '"id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodVersion1(self):
        result = jsonrpc.encodeRequest('method', version=1.0)
        pattern = '\{"method": "method", "id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodVersion2(self):
        result = jsonrpc.encodeRequest('method', version=2.0)
        pattern = '\{"jsonrpc": "2.0", "method": "method", "id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodVersion2int(self):
        result = jsonrpc.encodeRequest('method', version=2)
        pattern = '\{"jsonrpc": "2.0", "method": "method", "id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodVersion3(self):
        result = jsonrpc.encodeRequest('method', version=3)
        pattern = '\{"method": "method", "id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_methodIdVersion(self):
        result = jsonrpc.encodeRequest('method', version=2.0, id_=123)
        expected = '{"jsonrpc": "2.0", "method": "method", "id": 123}'
        self.assertEquals(result, expected)

    def test_methodArgsId(self):
        result = jsonrpc.encodeRequest('method', 'abcdef', id_=123)
        expected = '{"params": "abcdef", "method": "method", "id": 123}'
        self.assertEquals(result, expected)

    def test_methodArgsVersion2(self):
        result = jsonrpc.encodeRequest('method', 'abcdef', version=2)
        pattern = '\{"jsonrpc": "2.0", "params": "abcdef", "method": "method", '
        pattern += '"id": \d+\}'
        self.assertTrue(re.match(pattern, result))

    def test_all(self):
        result = jsonrpc.encodeRequest('method', 'abcdef', id_=123, version=2.0)
        expected = '{"jsonrpc": "2.0", "params": "abcdef", "method": "method", '
        expected += '"id": 123}'
        self.assertEquals(result, expected)

