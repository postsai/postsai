#! /usr/bin/python

import cgi
import json
import MySQLdb as mdb

import config

def convert_to_builtin_type(obj):
    return str(obj)

class Postsai:

    def query(self):
        """Executes the database query and prints the result"""

        conn = mdb.connect(config.config_db_host, config.config_db_user, config.config_db_password, config.config_db_database)
        cursor = conn.cursor()
        cursor.execute(self.sql, self.data)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()

        # Workaround UTF-8 data in an ISO-8859-1 column
        result = []
        for row in rows:
            tmp = []
            result.append(tmp);
            for col in row:
                tmp.append(str(col).decode("UTF-8", errors='replace'))
        return result


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

        self.sql = self.sql + " ORDER BY checkins.ci_when DESC LIMIT 1000"


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
            self.sql = self.sql + " AND ci_when >= %s AND ci_when <= %s"
            sel.data.append(form.getfirst("mindate")) 
            sel.data.append(form.getfirst("maxdate")) 


    def process(self):
        print "Content-Type: text/json; charset='utf-8'\r"
        print "\r"
        form = cgi.FieldStorage()
        self.create_query(form)
        result = self.query()
        print json.dumps(result, default=convert_to_builtin_type)


Postsai().process()