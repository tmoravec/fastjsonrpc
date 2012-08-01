import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from StringIO import StringIO
from twisted.trial.unittest import TestCase
from twisted.web.server import NOT_DONE_YET
from twisted.web.test.test_web import DummyRequest
from twisted.enterprise import adbapi
from twisted.internet.defer import succeed

from fastjsonrpc.server import JSONRPCServer

# two types: 1) start server and use client, 2) test render(...) directly
#
# 1) a) prepare methods to test
#    b) start on random port in setUp
#    c) test via (async) client
#    d) stop in tearDown
#
# 2) a) mock Request object-.content, .content.seek, .write, .finish, .setHeader
#    b) test render() directly
#    c) prepare various JSONs
#

def _render(resource, request):
    result = resource.render(request)
    if isinstance(result, str):
        request.write(result)
        request.finish()
        return succeed(None)
    elif result is NOT_DONE_YET:
        if request.finished:
            return succeed(None)
        else:
            return request.notifyFinish()
    else:
        raise ValueError('Unexpected return value: %r' % (result,))


class DummyServer(JSONRPCServer):

    def jsonrpc_echo(self, data):
        return data

    def jsonrpc_sql(self):
        def firstRow(sql_result):
            return sql_result[0]

        sql = 'SELECT User FROM user LIMIT 1'
        dbpool = adbapi.ConnectionPool('MySQLdb', 'localhost', user='root',
                                       passwd='', db='mysql')
        d = dbpool.runQuery(sql)
        d.addCallback(firstRow)
        return d


class TestRender(TestCase):

    def setUp(self):
        self.srv = DummyServer()

    def test_emptyRequest(self):
        request = DummyRequest([''])
        request.content = StringIO('')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_malformed(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql", "id')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_contentType(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": 1, ' +
                                   '"params": ["ab"]}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.outgoingHeaders['content-type'],
                              'application/json')

        d.addCallback(rendered)
        return d

    def test_contentLength(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": 1, ' +
                                   '"params": ["ab"]}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(len(request.written[0]),
                              request.outgoingHeaders['content-length'])

        d.addCallback(rendered)
        return d

    def test_echoOk(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": 1, ' +
                                   '"params": ["ab"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": 1, "result": "ab"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_sqlOk(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql", "id": 1}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": 1, "result": ["root"]}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_notificationV1(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql"}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_notificationV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql", "jsonrpc": "2.0"}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_noSuchMethodNoId(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "aaaa"}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_noSuchMethodV1(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "aaaa", "id": 1}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"result": null, "id": 1, "error": ' + \
                       '{"message": "Method aaaa not found", ' + \
                       '"code": -32601}}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_noSuchMethodV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "aaaa", "id": 1, ' + \
                                   '"jsonrpc": "2.0"}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"jsonrpc": "2.0", "id": 1, "error": ' + \
                       '{"message": "Method aaaa not found", ' + \
                       '"code": -32601}}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_wrongParams(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql", "id": 1, ' +
                                   '"params": ["aa", "bb"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"result": null, "id": 1, "error": {"message": ' + \
                       '"jsonrpc_sql() takes exactly 1 argument (3 given)"' + \
                       ', "code": -32602}}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

