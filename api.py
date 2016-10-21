#! /usr/bin/python

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

import calendar
import cgi
import json
import MySQLdb as mdb
import re
import sys
import subprocess
import datetime
from os import environ

import config

from backend.cache import Cache
from backend.db import PostsaiDB
from backend.cvs import PostsaiCommitViewer
from backend.query import Postsai
from backend.importer import PostsaiImporter



if __name__ == '__main__':
    if environ.has_key('REQUEST_METHOD') and environ['REQUEST_METHOD'] == "POST":
        PostsaiImporter(vars(config), json.loads(sys.stdin.read())).import_from_webhook()
    else:
        form = cgi.FieldStorage()
        if form.getfirst("method", "") == "commit":
            PostsaiCommitViewer(vars(config)).process()
        else:
            Postsai(vars(config)).process()

