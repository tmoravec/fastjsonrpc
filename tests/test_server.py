import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# two types: 1) start server and use client, 2) test render(...) directly
#
# 1) a) prepare methods to test
#    b) start on random port in setUp
#    c) test via (async) client
#    d) stop in tearDown
#
# 2) a) mock Request object-.content, .content.seek, .write, .finish, .setHeader
#    b) test render() directly
#    c) prepare various JSONs
#
