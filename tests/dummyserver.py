import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.enterprise import adbapi
from zope.interface import implements
from twisted.cred.portal import IRealm
from twisted.web.resource import IResource
from fastjsonrpc.server import JSONRPCServer

DBFILE = 'sqlite.db'


class DummyServer(JSONRPCServer):

    def jsonrpc_echo(self, data):
        return data

    def jsonrpc_sql(self):
        """ This is ugly, I'm aware. """

        def selectCount(_):
            sql = 'SELECT COUNT(*) FROM test'
            d = dbpool.runQuery(sql)
            return d

        sql = 'CREATE TABLE test (id int, value text, other_value text)'
        dbpool = adbapi.ConnectionPool('sqlite3', DBFILE)
        d = dbpool.runQuery(sql)
        d.addCallback(selectCount)
        return d

    def jsonrpc_returnNone(self):
        return None


class AuthDummyServer(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, DummyServer(), lambda: None)

        raise NotImplementedError()
