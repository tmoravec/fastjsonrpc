#!/usr/bin/env python
"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import distutils.core

with open("README.md") as readme:
    long_description = readme.read()

distutils.core.setup(
    name = "fastjsonrpc",
    version = "0.2.3",
    packages = ["fastjsonrpc"],
    author = "Tadeas Moravec",
    author_email = "tadeas.moravec@email.cz",
    url = "http://github.com/tadeas/fastjsonrpc",
    license = "http://www.apache.org/licenses/LICENSE-2.0",
    description = "A library for writing asynchronous JSON-RPC servers and clients in Python, using Twisted.",
    long_description = long_description,
    classifiers = [
        'Development Status :: 4 - Beta',
        ]
)
