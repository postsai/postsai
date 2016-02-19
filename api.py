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
        return rows


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
        WHERE 1=1 ORDER BY checkins.ci_when DESC LIMIT 1000"""


    def process(self):
        print "Content-Type: text/json; charset='utf-8'\r"
        print "\r"
        form = cgi.FieldStorage()
        self.create_query(form)
        result = self.query()
        print json.dumps(result, default=convert_to_builtin_type)


Postsai().process()