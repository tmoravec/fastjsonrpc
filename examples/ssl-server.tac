"""
We expect the SSL key and certificate in ssl-keys/server.key and
ssl-keys/server.crt.
"""

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from fastjsonrpc.server import JSONRPCServer

from twisted.web.server import Site
from twisted.application import service
from twisted.application import internet
from twisted.enterprise import adbapi
from twisted.internet import ssl


class Example(JSONRPCServer):
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

application = service.Application('Example JSON-RPC server')
root = Example()
site = Site(root)

factory = ssl.DefaultOpenSSLContextFactory('ssl-keys/server.key',
                                           'ssl-keys/server.crt')
server = internet.SSLServer(8999, site, factory)
server.setServiceParent(application)
