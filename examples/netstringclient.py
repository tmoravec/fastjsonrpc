import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.internet import reactor
from twisted.internet import defer
from twisted.python import log

from fastjsonrpc.netstringclient import Proxy


def printValue(value):
    print "Result: %s" % str(value)


def printError(error):
    print 'error', error.value


def shutDown(data):
    print "Shutting down reactor..."
    reactor.stop()


log.startLogging(sys.stdout)

dl = []
proxy = Proxy('127.0.0.1:8999', verbose=True)

d = proxy.callRemote('none')
d.addCallbacks(printValue, printError)
dl.append(d)

d = proxy.callRemote('none')
d.addCallbacks(printValue, printError)
dl.append(d)

d = proxy.callRemote('echo', 123)
d.addCallbacks(printValue, printError)
dl.append(d)

dl = defer.DeferredList(dl)
dl.addCallback(shutDown)

reactor.run()
