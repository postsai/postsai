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

from cache import Cache


class PostsaiDB:
    """Database access for postsai"""

    column_table_mapping = {
        "repository" : "repositories",
        "who" : "people",
        "dir" : "dirs",
        "file" : "files",
        "branch" : "branches",
        "description" : "descs",
        "hash": "commitids"
    }


    def __init__(self, config):
        """Creates a Postsai api instance"""

        self.config = config


    def connect(self):
        """connects to the database"""

        self.conn = mdb.connect(
            host    = self.config["db"]["host"],
            user    = self.config["db"]["user"],
            passwd  = self.config["db"]["password"],
            db      = self.config["db"]["database"],
            port    = self.config["db"].get("port", 3306),
            use_unicode = True,
            charset = "utf8")

        # checks whether this is a ViewVC database instead of a Bonsai database
        cursor = self.conn.cursor()
        cursor.execute("show tables like 'commits'")
        self.is_viewvc_database = (cursor.rowcount == 1)
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 500")
        cursor.close()
        self.conn.begin()


    def disconnect(self):
        """commits transactions and closes database connection"""

        self.conn.commit()
        self.conn.close()


    def rewrite_sql(self, sql):
        """rewrites SQL statements for ViewVC-query databases"""

        if self.is_viewvc_database:
            sql = sql.replace("checkins", "commits")
        return sql


    def query(self, sql, data, cursor_type=None):
        """queries the database"""

        cursor = self.conn.cursor(cursor_type)
        cursor.execute(self.rewrite_sql(sql), data)
        rows = cursor.fetchall()
        cursor.close()
        return rows


    def query_as_double_map(self, sql, key, data=None):
        """queries the database and returns a dict"""

        rows = self.query(sql, data, mdb.cursors.DictCursor)
        res = {}
        for row in rows:
            res[row[key]] = row
        return res


    @staticmethod
    def guess_repository_urls(row):
        """guesses the repository urls"""

        base = row["url"]
        base_url = base
        if (base_url.find(row["repository"]) == -1):
            base_url = base_url + "/" + row["repository"]

        file_url = ""
        commit_url = ""
        tracker_url = ""
        icon_url = ""
        repository_url = row["repository_url"]

        # GitHub, Gitlab
        if base_url.find("https://github.com/") > -1 or base_url.find("gitlab") > -1:
            commit_url = base_url + "/commit/[commit]"
            file_url = base_url + "/blob/[commit]/[file]"
            tracker_url = base_url + "/issues/$1"

        # SourceForge
        elif base_url.find("://sourceforge.net") > -1:
            if row["revision"].find(".") == -1 and len(row["revision"]) < 30:  # Subversion
                commit_url = "https://sourceforge.net/[repository]/[commit]/"
                file_url = "https://sourceforge.net/[repository]/[commit]/tree/[file]"
            else: # CVS, Git
                commit_url = "https://sourceforge.net/[repository]/ci/[commit]/"
                file_url = "https://sourceforge.net/[repository]/ci/[revision]/tree/[file]"
            icon_url = "https://a.fsdn.com/allura/[repository]/../icon"

        # CVS
        elif row["revision"].find(".") > -1:  # CVS
            commit_url = "commit.html?repository=[repository]&commit=[commit]"
            file_url = base + "/[repository]/[file]?revision=[revision]&view=markup"

        # Git
        else: # git instaweb
            commit_url = base + "/?p=[repository];a=commitdiff;h=[commit]"
            file_url = base + "/?p=[repository];a=blob;f=[file];hb=[commit]"

        return (base_url, repository_url, file_url, commit_url, tracker_url, icon_url)


    def call_setup_repository(self, row, guess):
        """let the configruation overwrite guessed repository info"""

        if not "setup_repository" in self.config:
            return guess
        return self.config["setup_repository"](row, *guess)


    def extra_data_for_key_tables(self, cursor, column, row, value):
        """provides additional data that should be stored in lookup tables"""

        extra_column = ""
        extra_data = ""
        data = [value]
        if column == "description":
            extra_column = ", hash"
            extra_data = ", %s"
            data.append(len(value))
        elif column == "repository":
            extra_column = ", base_url, repository_url, file_url, commit_url, tracker_url, icon_url"
            extra_data = ", %s, %s, %s, %s, %s, %s"
            data.extend(self.call_setup_repository(row, self.guess_repository_urls(row)))
        elif column == "hash":
            extra_column = ", authorid, committerid, co_when"
            extra_data = ", %s, %s, %s"
            self.fill_id_cache(cursor, "who", row, row["author"])
            self.fill_id_cache(cursor, "who", row, row["committer"])
            data.extend((self.cache.get("who", row["author"]),
                         self.cache.get("who", row["committer"]),
                         row["co_when"]))

        return data, extra_column, extra_data


    def fill_id_cache(self, cursor, column, row, value):
        """fills the id-cache"""

        if self.cache.has(column, value):
            return

        data, extra_column, extra_data = self.extra_data_for_key_tables(cursor, column, row, value)

        sql = "SELECT id FROM " + self.column_table_mapping[column] + " WHERE " + column + " = %s"
        cursor.execute(sql, [value])
        rows = cursor.fetchall()
        if len(rows) > 0:
            self.cache.put(column, value, rows[0][0])
        else:
            sql = "INSERT INTO " + self.column_table_mapping[column] + " (" + column + extra_column + ") VALUE (%s" + extra_data + ")"
            cursor.execute(sql, data)
            self.cache.put(column, value, cursor.lastrowid)


    def import_data(self, head, rows):
        """Imports data"""

        self.connect()
        self.cache = Cache()
        cursor = self.conn.cursor()

        sql = """INSERT INTO importactions (remote_addr, remote_user, sender_addr, sender_user, ia_when) VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, [
            environ.get("REMOTE_ADDR", ""), environ.get("REMOTE_USER", ""),
            head["sender_addr"],head["sender_user"],
            datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        ])
        importactionid = cursor.lastrowid

        for row in rows:
            for key in self.column_table_mapping:
                self.fill_id_cache(cursor, key, row, row[key])

        for row in rows:
            sql = """INSERT IGNORE INTO checkins(type, ci_when, whoid, repositoryid, dirid, fileid, revision, branchid, addedlines, removedlines, descid, stickytag, commitid, importactionid)
                 VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(self.rewrite_sql(sql), [
                row["type"],
                row["ci_when"],
                self.cache.get("who", row["who"]),
                self.cache.get("repository", row["repository"]),
                self.cache.get("dir", row["dir"]),
                self.cache.get("file", row["file"]),
                row["revision"],
                self.cache.get("branch", row["branch"]),
                row["addedlines"],
                row["removedlines"],
                self.cache.get("description", row["description"]),
                "",
                self.cache.get("hash", row["commitid"]),
                str(importactionid)
                ])

        cursor.close()
        self.disconnect()
