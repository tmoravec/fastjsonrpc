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
        self.json_echo = StringIO('{"method": "echo", "id": 1, ' +
                                  '"params": ["ab"]}')
        self.json_sql = StringIO('{"method": "sql", "id": 1}')


    def test_contentType(self):
        request = DummyRequest([''])
        request.content = self.json_echo
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(request.outgoingHeaders['content-type'],
                              'application/json')

        d.addCallback(rendered)
        return d

    def test_contentLength(self):
        request = DummyRequest([''])
        request.content = self.json_echo
        d = _render(self.srv, request)

        def rendered(_):
            self.assertEquals(len(request.written[0]),
                              request.outgoingHeaders['content-length'])

        d.addCallback(rendered)
        return d

    def test_echoOk(self):
        request = DummyRequest([''])
        request.content = self.json_echo
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": 1, "result": "ab"}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d

    def test_sqlOk(self):
        request = DummyRequest([''])
        request.content = self.json_sql
        d = _render(self.srv, request)

        def rendered(_):
            expected = '{"error": null, "id": 1, "result": ["root"]}'
            self.assertEquals(request.written[0], expected)

        d.addCallback(rendered)
        return d
