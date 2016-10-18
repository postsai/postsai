#! /usr/bin/python

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

