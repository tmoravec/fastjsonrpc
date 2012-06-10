import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from fastjsonrpc.server import JSONRPCServer

from twisted.web.server import Site
from twisted.application import service
from twisted.application import internet


class Example(JSONRPCServer):
    def jsonrpc_echo(self, data):
        return data

    def jsonrpc_add(self, a, b):
        return a + b


application = service.Application("Example JSON-RPC server")
root = Example()
site = Site(root)

server = internet.TCPServer(8999, site)
server.setServiceParent(application)
