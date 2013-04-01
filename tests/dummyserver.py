import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.enterprise import adbapi
from zope.interface import implements
from twisted.cred.portal import IRealm
from twisted.web.resource import IResource
from fastjsonrpc.server import JSONRPCServer

MYSQL_SERVER = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWD = ''


class DummyServer(JSONRPCServer):

    def jsonrpc_echo(self, data):
        return data

    def jsonrpc_sql(self):
        def firstRow(sql_result):
            return sql_result[0]

        sql = 'SELECT User FROM user LIMIT 1'
        dbpool = adbapi.ConnectionPool('MySQLdb', MYSQL_SERVER, MYSQL_USER,
                                       MYSQL_PASSWD, db='mysql')
        d = dbpool.runQuery(sql)
        d.addCallback(firstRow)
        return d

    def jsonrpc_returnNone(self):
        return None


class AuthDummyServer(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, DummyServer(), lambda: None)

        raise NotImplementedError()
