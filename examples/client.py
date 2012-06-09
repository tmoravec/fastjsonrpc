import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.internet import reactor

from fastjsonrpc.client import Proxy

def printValue(value):
    print "Result: %s" % str(value)


def printError(error):
    print 'error', error


def shutDown(data):
    print "Shutting down reactor..."
    reactor.stop()

address = 'http://localhost:8999'

proxy = Proxy(address)
d = proxy.callRemote('echo', 'ajajaj')

d.addCallbacks(printValue, printError)
d.addBoth(shutDown)

reactor.run()
