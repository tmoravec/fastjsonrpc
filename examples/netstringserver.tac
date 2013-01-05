import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from fastjsonrpc.netstringserver import JSONRPCServer

from twisted.internet.protocol import Factory
from twisted.enterprise import adbapi
from twisted.application import service
from twisted.application import internet


class Example(JSONRPCServer):

    def __init__(self):
        JSONRPCServer.__init__(self, True)

    def jsonrpc_echo(self, data):
        return data

    def jsonrpc_none(self):
        raise Exception('vyjimka')

    def jsonrpc_add(self, a, b):
        return a + b

    def jsonrpc_mysql_first_user(self):
        def capitalize(sql_result):
            if sql_result:
                return sql_result[0][0].upper()
            else:
                return None

        sql = 'SELECT User FROM user LIMIT 1'
        dbpool = adbapi.ConnectionPool('MySQLdb', 'localhost', user='root',
                                       passwd='', db='mysql')
        d = dbpool.runQuery(sql)
        d.addCallback(capitalize)
        return d


factory = Factory()
factory.protocol = Example

application = service.Application('Example JSON-RPC server')
server = internet.TCPServer(8999, factory)
server.setServiceParent(application)
