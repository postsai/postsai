# The MIT License (MIT)
# Copyright (c) 2016-2026 Postsai
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


from urllib.parse import parse_qs
from os import environ


class Request:
    """Represents parsed request parameters."""

    def __init__(self, params):
        """initialize the request object"""
        self._params = params or {}

    @classmethod
    def from_environ(cls, env=None):
        """create a Request object from the CGI environment"""
        env = env or environ
        params = parse_qs(env.get('QUERY_STRING', ''), keep_blank_values=True)
        return cls(params)

    def getfirst(self, name, default=None):
        """get the first value"""
        v = self._params.get(name)
        if v:
            return v[0]
        return default

    def getlist(self, name):
        """get the list of values"""
        return self._params.get(name, [])

    def getvalue(self, name, default=None):
        """get the value or the list of values"""
        v = self._params.get(name)
        if v is None:
            return default
        if len(v) == 1:
            return v[0]
        return v
