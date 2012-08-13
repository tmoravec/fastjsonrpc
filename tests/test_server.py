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

    def test_idStrV1(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": "abcd", ' +
                                   '"params": ["ab"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": "abcd", "result": "ab"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_idStrV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": "abcd", ' +
                                   '"params": ["ab"], "jsonrpc": "2.0"}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"jsonrpc": "2.0", "id": "abcd", ' + \
                       '"result": "ab"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_caseSensitiveMethodV1(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "ECHO", "id": "ABCD", ' +
                                   '"params": ["AB"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"result": null, "id": "ABCD", "error": {"message": ' +\
                       '"Method ECHO not found", "code": -32601}}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_caseSensitiveParamsV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": "ABCD", ' +
                                   '"params": ["AB"], "jsonrpc": "2.0"}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"jsonrpc": "2.0", "id": "ABCD", "result": "AB"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_invalidMethodCaseSensitive(self):
        request = DummyRequest([''])
        request.content = StringIO('{"METHOD": "echo", "id": "ABCD", ' +
                                   '"params": ["AB"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"result": null, "id": "ABCD", "error": ' + \
                       '{"message": "Invalid method type", "code": -32600}}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_invalidIdCaseSensitive(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "ID": "ABCD", ' +
                                   '"params": ["AB"]}')
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.written, [])

        d.addCallback(rendered)
        return d

    def test_invalidParamsCaseSensitive(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": "ABCD", ' +
                                   '"PARAMS": ["AB"]}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"result": null, "id": "ABCD", "error": ' + \
                       '{"message": "jsonrpc_echo() takes exactly 2 ' + \
                       'arguments (1 given)", "code": -32602}}'
            self.assertEquals(request.written[0], expected)

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

    def test_echoOkV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "echo", "id": 1, ' +
                                   '"params": ["ab"], "jsonrpc": "2.0"}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"jsonrpc": "2.0", "id": 1, "result": "ab"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_sqlOkV1(self):
        request = DummyRequest([''])
        request.content = StringIO('{"method": "sql", "id": 1}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": 1, "result": ["root"]}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_sqlOkV2(self):
        request = DummyRequest([''])
        request.content = StringIO('{"jsonrpc": "2.0", "method": "sql", '
                                   '"id": 1}')
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"jsonrpc": "2.0", "id": 1, "result": ["root"]}'
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

