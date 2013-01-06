import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from twisted.internet import reactor

from fastjsonrpc.netstringclient import Proxy


def printError(error):
    print 'error:', error.value
    reactor.stop()


def printResult(result):
    print 'response:', result
    reactor.stop()

proxy = Proxy('127.0.0.1:8999', verbose=True)
d = proxy.callRemote('none')
d.addCallback(printResult)
d.addErrback(printError)

reactor.run()
