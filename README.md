Introduction
============

A library for writing asynchronous JSON-RPC servers and clients in Python,
using Twisted. It aims to be as simple and easy to understand (and hack)
as possible.

Read more about JSON-RPC at http://www.jsonrpc.org/


Features
========

* Support for HTTP and HTTPS as protocol (via twisted.web), more might come
  in the future.

* Support for HTTP authentization - only basic, not digest; use SSL for better
  security.

* Full standards compliance.

* Support both JSON-RPC standards at once - great if you don't control your
  clients.

* 'Just work' with various clients (i.e. PHP, C++, JavaScript...).

* Detailed examples :-) .


TODO
====

* More tests, better (functionality) coverage. This applies to every project,
  always :-) .

* Finish support for netstring protocol.


Notes
=====

* JSON is well readable for a human. It's easy to use Wireshark
  (www.wireshark.org) or similar for debugging.

* JSON-RPC version 1 doesn't talk about batch requests. In order to support both
  standards at once, fastjsonrpc supports it just like in version 2. It ties
  JSON-RPC version to the method call, not the request as a whole.

* I didn't test the JSON Class hinting, as mentioned in the version 1 spec. I
  leave this to the JSON parsing capabilities of respective libraries.

