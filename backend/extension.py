# The MIT License (MIT)
# Copyright (c) 2016-2021 Postsai
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

import os

class ExtensionManager:
    """Manages extensions"""

    def __init__(self):
        """loads extensions"""

        self.extensions = []

        extensions_folder = "extensions"
        for extension_folder in os.listdir(extensions_folder):
            if os.path.isfile(extensions_folder + "/" + extension_folder + "/__init__.py"):
                mod = __import__("extensions." + extension_folder, fromlist=["Extension"])
                self.extensions.append(getattr(mod, "Extension")())


    def call_all(self, method, params):
        """invokes a method on all extensions"""

        for extension in self.extensions:
            method_pointer = getattr(extension, method, None)
            if method_pointer != None:
                method_pointer(*params)

    @staticmethod
    def list_extension_files(filename):
        """returns a list of all files with the specified name that exist in extensions"""

        res = []
        extensions_folder = "extensions"

        for extension_folder in os.listdir(extensions_folder):
            possible_filename = extensions_folder + "/" + extension_folder + "/" + filename
            if os.path.isfile(possible_filename):
                res.append(possible_filename)

        return res
