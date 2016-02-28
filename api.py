#! /usr/bin/python

import cgi
import json
import MySQLdb as mdb
import re

import config

def convert_to_builtin_type(obj):
    return str(obj)

class Cache:
    """Cache"""

    cache = {};

    def put(self, type, key, value):
        """adds an entry to the cache"""

        if not type in self.cache:
            self.cache[type] = {}
        self.cache[type][key] = value;


    def get(self, type, key):
        """gets an entry from the cache"""

        if not type in self.cache:
            return None;
        return self.cache[type][key];



class PostsaiDB:
    """Database access for postsai"""

    column_table_mapping = {
        "repository" : "repositories",
        "who" : "people",
        "dir" : "dirs",
        "file" : "files",
        "branch" : "branches",
        "description" : "descs"
    }


    def __init__(self, config):
        """Creates a Postsai api instance"""

        self.config = config


    def connect(self):
        self.conn = mdb.connect(self.config['db']['host'], self.config['db']['user'], 
                           self.config['db']['password'], self.config['db']['database'])

        # checks whether this is a ViewVC database instead of a Bonsai database
        cursor = self.conn.cursor()
        cursor.execute("show tables like 'commits'")
        self.is_viewvc_database = (cursor.rowcount == 1)


    def rewrite_sql(self, sql):
        if self.is_viewvc_database:
            sql = sql.replace("checkins", "commits")
        return sql


    def update_database_structure(self):
        """alters the database structure"""

        cursor = self.conn.cursor()

        # increase column width of checkins
        cursor.execute(self.rewrite_sql("SELECT revision FROM checkins WHERE 1=0"))
        size = cursor.description[0][3]
        if size < 50:
            cursor.execute(self.rewrite_sql("ALTER TABLE checkins CHANGE revision revision VARCHAR(50);"))
        
        cursor.close()


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


    def one_shot_query(self, sql, data):
        """Executes the database query and prints the result"""

        self.connect()
        self.conn.begin();
        cursor = self.conn.cursor()


        cursor.execute(self.rewrite_sql(sql), data)
        rows = cursor.fetchall()
        self.conn.commit()
        self.conn.close()
        return self.fix_encoding_of_result(rows)


    def fill_id_cache(self, cursor, column, value):
        """fills the id-cache"""
        data = [value]
        extra_column = ""
        extra_data = ""

        # Special case for description column
        if column == "description":
            extra_column = ", hash"
            extra_data = ", %s"
            data.append(len(value))

        sql = "SELECT id FROM " + self.column_table_mapping[column] + " WHERE " + column + " = %s FOR UPDATE"
        cursor.execute(sql, [value])
        rows = cursor.fetchall()
        if len(rows) > 0:
            self.cache.put(column, value, rows[0][0])
        else:
            sql = "INSERT INTO " + self.column_table_mapping[column] + " (" + column + extra_column + ") VALUE (%s" + extra_data + ")"
            cursor.execute(sql, data)
            self.cache.put(column, value, cursor.lastrowid)


    def import_data(self, rows):
        """Imports data"""

        self.connect()
        self.conn.begin()
        self.cache = Cache()
        cursor = self.conn.cursor()

        for row in rows:
            for key, table in self.column_table_mapping.items():
                self.fill_id_cache(cursor, key, row[key])
        
        for row in rows:
            sql = """INSERT INTO checkins(type, ci_when, whoid, repositoryid, dirid, fileid, revision, branchid, addedlines, removedlines, descid, stickytag) 
                 VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, [
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
                ""
                ])

        cursor.close()
        self.conn.commit()
        self.conn.close()
        


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
                "data" : PostsaiDB(self.config).one_shot_query(self.sql, self.data)
            }

        print(json.dumps(result, default=convert_to_builtin_type))


    def import_from_webhook(self, data):
        actionMap = {
            "Add" : "added",
            "Remove" : "removed",
            "Change" : "modified"
        }
        rows = []
        branch = data['ref'][data['ref'].rfind("/")+1:]
        for commit in data['commits']:
            for type in ("Change", "Add", "Remove"):
                for full_path in commit[actionMap[type]]:

                    dir = full_path[0:full_path.rfind("/")]
                    file = full_path[full_path.rfind("/")+1:]
                    row = {
                        "type" : type,
                        "ci_when" : commit['timestamp'], 
                        "who" : commit['author']['email'],
                        "repository" : data['repository']['full_name'],
                        "dir" : dir,
                        "file" : file,
                        "revision" : commit['id'],
                        "branch" : branch,
                        "addedlines" : "0",
                        "removedlines" : "0",
                        "description" : commit['message']
                    }
                    rows.append(row)
        db = PostsaiDB(self.config)
        db.import_data(rows)



if __name__ == '__main__':
    if cgi.FieldStorage().getfirst("date", "") == "":
        Postsai(vars(config)).import_from_webhook(json.loads(sys.stdin.read()))
    else:
        Postsai(vars(config)).process()

