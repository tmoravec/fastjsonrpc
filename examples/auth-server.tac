import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from fastjsonrpc.server import JSONRPCServer

from zope.interface import implements

from twisted.cred.portal import IRealm, Portal
from twisted.web.resource import IResource
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory
from twisted.cred.checkers import FilePasswordDB
from twisted.application import service
from twisted.web.server import Site
from twisted.application import internet
from twisted.enterprise import adbapi

MYSQL_SERVER = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWD = ''


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
        dbpool = adbapi.ConnectionPool('MySQLdb', MYSQL_SERVER,
                                       user=MYSQL_USER, passwd=MYSQL_PASSWD,
                                       db='mysql')
        d = dbpool.runQuery(sql)
        d.addCallback(capitalize)
        return d

class AuthRPCServer(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, Example(), lambda: None)

        raise NotImplementedError()

portal = Portal(AuthRPCServer(), [FilePasswordDB('httpd.password')])
credentialFactory = BasicCredentialFactory('localhost')
resource = HTTPAuthSessionWrapper(portal, [credentialFactory])
site = Site(resource)

application = service.Application('Example JSON-RPC server')
server = internet.TCPServer(8999, site)
server.setServiceParent(application)
