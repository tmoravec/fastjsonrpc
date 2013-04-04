Introduction
============

A library for writing asynchronous JSON-RPC servers and clients in Python,
using Twisted. It aims to be as simple and easy to understand (and hack)
as possible.

Read more about JSON-RPC at http://www.jsonrpc.org/


Features
========

* Support for HTTP and HTTPS as protocol (via twisted.web) and for more
  lightweight netstring (see http://cr.yp.to/proto/netstrings.txt )

* Support for HTTP authentization - only basic, not digest; use SSL for
  encrypted credentials.

* Full standards compliance.

* Support both JSON-RPC standards at once - great if you don't control your
  clients.

* 'Just work' with various clients (i.e. PHP, C++, JavaScript...).

* Detailed examples :-) .


TODO
====

* More tests, better (functionality) coverage. This applies to every project,
  always :-) .

* Refactoring, mostly tests.
    * test_server and test_jsonrpc
    * test_client and test_netstringclient


Notes
=====

* JSON is well readable for a human. It's easy to use Wireshark
  (www.wireshark.org) or similar for debugging.

* JSON-RPC version 1 doesn't talk about batch requests. In order to support both
  standards at once, fastjsonrpc supports it just like in version 2. It ties
  JSON-RPC version to the method call, not the request as a whole.

* I didn't test the JSON Class hinting, as mentioned in the version 1 spec. I
  leave this to the JSON parsing capabilities of respective libraries.

* SSL client test raises an error after shutDown. Looks like a bug in Trial
  and we can ignore it.
