# The MIT License (MIT)
# Copyright (c) 2016 Postsai
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


class Cache:
    """Cache"""

    cache = {}

    def put(self, entity_type, key, value):
        """adds an entry to the cache"""

        if not entity_type in self.cache:
            self.cache[entity_type] = {}
        self.cache[entity_type][key] = value


    def get(self, entity_type, key):
        """gets an entry from the cache"""

        if not entity_type in self.cache:
            return None
        return self.cache[entity_type][key]


    def has(self, entity_type, key):
        """checks whether an item is in the cache"""

        if not entity_type in self.cache:
            return False
        return key in self.cache[entity_type]
