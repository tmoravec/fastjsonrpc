import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.enterprise import adbapi
from fastjsonrpc.server import JSONRPCServer


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

    def jsonrpc_returnNone(self):
        return None
