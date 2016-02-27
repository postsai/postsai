#! /usr/bin/python

import cgi
import json
import MySQLdb as mdb
import re

import config

def convert_to_builtin_type(obj):
    return str(obj)

class PostsaiDB:
    """Databaes access for postsai"""


    def __init__(self, config):
        """Creates a Postsai api instance"""

        self.config = config


    def is_viewvc_database(self, cursor):
        """checks whether this is a Viewvc database instead of a Bonsai database"""

        cursor.execute("show tables like 'commits'")
        return cursor.rowcount == 1


    def fix_encoding_of_result(self, rows):
        """ Workaround UTF-8 data in an ISO-8859-1 column"""

        result = []
        for row in rows:
            tmp = []
            result.append(tmp);
            for col in row:
                try:
                    tmp.append(str(col).decode("UTF-8"))
                except UnicodeDecodeError:
                    tmp.append(str(col).decode("ISO-8859-1"))
        return result


    def query(self, sql, data):
        """Executes the database query and prints the result"""

        conn = mdb.connect(self.config['db']['host'], self.config['db']['user'], self.config['db']['password'], self.config['db']['database'])
        cursor = conn.cursor()

        if (self.is_viewvc_database(cursor)):
            sql = sql.replace("checkins", "commits")

        cursor.execute(sql, data)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()
        return self.fix_encoding_of_result(rows)




class Postsai:

    def __init__(self, config):
        """Creates a Postsai api instance"""

        self.config = config


    def validate_input(self, form):
        """filter inputs, e. g. for privacy reasons"""

        if not "filter" in self.config:
            return ""

        for key, filter in self.config['filter'].items():
            value = form.getfirst(key, "")
            if value != "":
                if value.startswith("^") and value.endswith("$"):
                    value = value[1:-1]
                if re.match(filter, value) == None:
                    return "Missing permissions for query on column \"" + key + "\""
        
        return ""



    def create_query(self, form):
        """creates the sql statement"""

        self.data = []
        self.sql = """SELECT repositories.repository, checkins.ci_when, people.who, concat(concat(dirs.dir, '/'), files.file), 
        checkins.revision, branches.branch, concat(concat(checkins.addedlines, '/'), checkins.removedlines), descs.description, repositories.repository
        FROM checkins 
        JOIN branches ON checkins.branchid = branches.id
        JOIN descs ON checkins.descid = descs.id
        JOIN dirs ON checkins.dirid = dirs.id
        JOIN files ON checkins.fileid = files.id
        JOIN people ON checkins.whoid = people.id
        JOIN repositories ON checkins.repositoryid = repositories.id
        WHERE 1=1 """

        self.create_where_for_column("branch", form, "branch")
        self.create_where_for_column("dir", form, "dir")
        self.create_where_for_column("description", form, "description")
        self.create_where_for_column("file", form, "file")
        self.create_where_for_column("who", form, "who")
        self.create_where_for_column("cvsroot", form, "repository")
        self.create_where_for_column("repository", form, "repository")

        self.create_where_for_date(form)

        self.sql = self.sql + " ORDER BY checkins.ci_when DESC"


    def create_where_for_column(self, column, form, internal_column):
        """create the where part for the specified column with data from the request"""
        
        value = form.getfirst(column, "")
        if (value == ""):
            return ""

        # replace HEAD branch with empty string
        if (column == "branch" and value == "HEAD"):
            value = "" 

        type = form.getfirst(column+"type", "match")
        operator = '=';
        if (type == "match"):
            operator = '='
        elif (type == "regexp"):
            operator = "REGEXP"
        elif (type == "notregexp"):
            operator = "NOT REGEXP"
        self.sql = self.sql + " AND " + internal_column + " " + operator + " %s"
        self.data.append(value)

    
    def create_where_for_date(self, form):
        """parses the date parameters and adds them to the database query"""

        type = form.getfirst("date", "day")
        if (type == "all"):
            return
        elif (type == "day"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 DAY)"
        elif (type == "week"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 WEEK)"
        elif (type == "month"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 MONTH)"
        elif (type == "hours"):
            self.sql = self.sql + " AND ci_when >= DATE_SUB(NOW(),INTERVAL %s HOUR)"
            self.data.append(form.getfirst("hours"))
        elif (type == "explicit"):
            mindate = form.getfirst("mindate", "")
            if mindate != "":
                self.sql = self.sql + " AND ci_when >= %s"
                self.data.append(mindate) 
            maxdate = form.getfirst("maxdate", "")
            if maxdate != "":
                self.sql = self.sql + " AND ci_when <= %s"
                self.data.append(maxdate) 


    def process(self):
        """processes an API request"""

        print("Content-Type: text/json; charset='utf-8'\r")
        print("\r")
        form = cgi.FieldStorage()

        result = self.validate_input(form)

        if result == "":
            self.create_query(form)
            result = {
                "config" : self.config['ui'], 
                "data" : PostsaiDB(self.config).query(self.sql, self.data)
            }

        print(json.dumps(result, default=convert_to_builtin_type))

if __name__ == '__main__':
    Postsai(vars(config)).process()