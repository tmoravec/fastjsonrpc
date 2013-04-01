import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from fastjsonrpc.netstringserver import JSONRPCServer
from twisted.enterprise import adbapi

MYSQL_SERVER = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWD = ''


class DummyProtocol(JSONRPCServer):

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
        dbpool = adbapi.ConnectionPool('MySQLdb', MYSQL_SERVER,
                                       user=MYSQL_USER, passwd=MYSQL_PASSWD,
                                       db='mysql')
        d = dbpool.runQuery(sql)
        d.addCallback(capitalize)
        return d
