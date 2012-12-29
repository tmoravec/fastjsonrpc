import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.internet import reactor
from twisted.internet import defer

from fastjsonrpc.client import Proxy


def printValue(value):
    print "Result: %s" % str(value)


def printError(error):
    print 'error', error.value


def shutDown(data):
    print "Shutting down reactor..."
    reactor.stop()

address = 'http://localhost:8999'

proxy = Proxy(address)
ds = []

d = proxy.callRemote('echo', ['ajajaj', 'bjbjbj'])
d.addCallbacks(printValue, printError)
ds.append(d)

d = proxy.callRemote('add', 14, 15)
d.addCallbacks(printValue, printError)
ds.append(d)

d = proxy.callRemote('mysql_first_user')
d.addCallbacks(printValue, printError)
ds.append(d)

d = proxy.callRemote('none')
d.addCallbacks(printValue, printError)
ds.append(d)

ds = defer.DeferredList(ds)
ds.addCallback(shutDown)

reactor.run()
