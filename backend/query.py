import calendar
import cgi
import json
import MySQLdb as mdb
import re
import sys
import subprocess
import datetime
from os import environ

from db import PostsaiDB



def convert_to_builtin_type(obj):
    """return a string representation for JSON conversation"""

    return str(obj)



class Postsai:

    def __init__(self, config):
        """Creates a Postsai api instance"""

        self.config = config


    def validate_input(self, form):
        """filter inputs, e. g. for privacy reasons"""

        if not "filter" in self.config:
            return ""

        for key, condition_filter in self.config['filter'].items():
            value = form.getfirst(key, "")
            if value != "":
                if value.startswith("^") and value.endswith("$"):
                    value = value[1:-1]
                if re.match(condition_filter, value) == None:
                    return "Missing permissions for query on column \"" + key + "\""

        return ""


    def get_read_permission_pattern(self):
        """get read permissions pattern"""

        if not "get_read_permission_pattern" in self.config:
            return ".*"
        return self.config["get_read_permission_pattern"]()


    def create_query(self, form):
        """creates the sql statement"""

        self.data = [self.get_read_permission_pattern()]
        self.sql = """SELECT repositories.repository, checkins.ci_when, people.who, trim(leading '/' from concat(concat(dirs.dir, '/'), files.file)),
        revision, branches.branch, concat(concat(checkins.addedlines, '/'), checkins.removedlines), descs.description, repositories.repository, commitids.hash 
        FROM checkins 
        JOIN branches ON checkins.branchid = branches.id
        JOIN descs ON checkins.descid = descs.id
        JOIN dirs ON checkins.dirid = dirs.id
        JOIN files ON checkins.fileid = files.id
        JOIN people ON checkins.whoid = people.id
        JOIN repositories ON checkins.repositoryid = repositories.id
        LEFT JOIN commitids ON checkins.commitid = commitids.id
        WHERE repositories.repository REGEXP %s """

        self.create_where_for_column("branch", form, "branch")
        self.create_where_for_column("dir", form, "dir")
        self.create_where_for_column("description", form, "description")
        self.create_where_for_column("file", form, "file")
        self.create_where_for_column("who", form, "who")
        self.create_where_for_column("cvsroot", form, "repository")
        self.create_where_for_column("repository", form, "repository")
        self.create_where_for_column("commit", form, "commitids.hash")

        self.create_where_for_date(form)

        self.sql = self.sql + " ORDER BY checkins.ci_when DESC, checkins.branchid DESC, checkins.descid DESC, checkins.id DESC"
        limit = form.getfirst("limit", None)
        if limit:
            self.sql = self.sql + " LIMIT " + str(int(limit))


    @staticmethod
    def convert_operator(matchtype):
        """convert the operator into a database operator"""

        operator = '='
        if (matchtype == "match"):
            operator = '='
        elif (matchtype == "regexp" or matchtype == "search"):
            # support for MySQL <= 5.5
            operator = "REGEXP"
        elif (matchtype == "notregexp"):
            operator = "NOT REGEXP"
        return operator


    def create_where_for_column(self, column, form, internal_column):
        """create the where part for the specified column with data from the request"""

        value = form.getfirst(column, "")
        if (value == ""):
            return ""

        # replace HEAD branch with empty string
        if (column == "branch" and value == "HEAD"):
            value = ""

        matchtype = form.getfirst(column+"type", "match")
        if internal_column == "description" and matchtype == "search" and not self.config.get("db", {}).get("old_mysql_version", False):
            self.sql = self.sql + " AND MATCH (" + internal_column + ") AGAINST (%s)"
        else:
            self.sql = self.sql + " AND " + internal_column + " " + self.convert_operator(matchtype) + " %s"
        self.data.append(value)


    def create_where_for_date(self, form):
        """parses the date parameters and adds them to the database query"""

        datetype = form.getfirst("date", "day")
        if (datetype == "none"):
            self.sql = self.sql + " AND 1 = 0"
        elif (datetype == "day"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 DAY)"
        elif (datetype == "week"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 WEEK)"
        elif (datetype == "month"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 MONTH)"
        elif (datetype == "hours"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL %s HOUR)"
            self.data.append(form.getfirst("hours"))
        elif (datetype == "explicit"):
            mindate = form.getfirst("mindate", "")
            if mindate != "":
                self.sql = self.sql + " AND ci_when >= %s"
                self.data.append(mindate)
            maxdate = form.getfirst("maxdate", "")
            if maxdate != "":
                self.sql = self.sql + " AND ci_when <= %s"
                self.data.append(maxdate)


    @staticmethod
    def are_rows_in_same_commit(data, pre):
        """determines if both database rows belong to the same SCM commit"""

        return data[9] == pre[9] and data[9] != None


    @staticmethod
    def convert_database_row_to_array(row):
        """converts a database result to an array"""

        tmp = []
        for col in row:
            tmp.append(col)
        return tmp


    @staticmethod
    def extract_commits(rows):
        """Merges query result rows to extract commits"""

        result = []
        lastRow = None
        for row in rows:
            tmp = Postsai.convert_database_row_to_array(row)
            tmp[3] = [tmp[3]]
            tmp[4] = [tmp[4]]
            if (lastRow == None):
                lastRow = tmp
                result.append(tmp)
            else:
                if Postsai.are_rows_in_same_commit(lastRow, tmp):
                    lastRow[3].append(tmp[3][0])
                    lastRow[4].append(tmp[4][0])
                else:
                    result.append(tmp)
                    lastRow = tmp

        return result


    def process(self):
        """processes an API request"""

        print("Content-Type: text/json; charset='utf-8'\r")
        print("Cache-Control: max-age=60\r")
        print("\r")
        form = cgi.FieldStorage()

        result = self.validate_input(form)

        if result == "":
            self.create_query(form)

            db = PostsaiDB(self.config)
            db.connect()
            rows = self.extract_commits(db.query(self.sql, self.data))
            repositories = db.query_as_double_map(
                "SELECT id, repository, base_url, file_url, commit_url, tracker_url, icon_url FROM repositories WHERE repositories.repository REGEXP %s",
                "repository",
                [self.get_read_permission_pattern()])
            db.disconnect()

            ui = {}
            if "ui" in self.config:
                ui = self.config['ui']

            result = {
                "config" : ui,
                "data" : rows,
                "repositories": repositories
            }

        print(json.dumps(result, default=convert_to_builtin_type))
