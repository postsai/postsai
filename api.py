#! /usr/bin/python

import cgi
import json
import MySQLdb as mdb
import re
import sys
from os import environ

import config

def convert_to_builtin_type(obj):
    return str(obj)

class Cache:
    """Cache"""

    cache = {};

    def put(self, entity_type, key, value):
        """adds an entry to the cache"""

        if not entity_type in self.cache:
            self.cache[entity_type] = {}
        self.cache[entity_type][key] = value;


    def get(self, entity_type, key):
        """gets an entry from the cache"""

        if not entity_type in self.cache:
            return None;
        return self.cache[entity_type][key];



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
        cursor.close()
        self.conn.begin();

    def disconnect(self):
        self.conn.commit()
        self.conn.close()

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

        # add columns to repositories table
        cursor.execute("SELECT * FROM repositories WHERE 1=0")
        if len(cursor.description) < 3:
            cursor.execute("ALTER TABLE repositories ADD (base_url VARCHAR(255), file_url VARCHAR(255), commit_url VARCHAR(255), icon_url VARCHAR(255), tracker_url VARCHAR(255))")

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


    def query(self, sql, data, cursor_type=None):
        cursor = self.conn.cursor(cursor_type)
        cursor.execute(self.rewrite_sql(sql), data)
        rows = cursor.fetchall()
        cursor.close()
        return rows


    def query_as_double_map(self, sql, key, data=None):
        rows = self.query(sql, data, mdb.cursors.DictCursor)
        res = {}
        for row in rows:
            res[row[key]] = row
        return res


    def guess_repository_urls(self, row):
        """guesses the repository urls"""

        base_url = row["url"]
        if (base_url.find(row["repository"]) == -1):
            base_url = base_url + "/" + row["repository"]

        file_url = ""
        commit_url = ""
        tracker_url = ""

        if base_url.find("https://github.com/") > -1 or base_url.find("gitlab") > -1:
            file_url = base_url + "/blob/[revision]/[file]"
            commit_url = base_url + "/commit/[revision]"
            tracker_url = base_url + "/issues/$1"

        elif base_url.find("://sourceforge.net") > -1:
            commit_url = "https://sourceforge.net/[repository]/ci/[revision]/"
            file_url = "https://sourceforge.net/[repository]/ci/[revision]/tree/[file]"
            icon_url = "https://a.fsdn.com/allura/p/[repository]/../icon"


        # CVS
            # file_url='http://cvs.example.com/cgi-bin/viewvc.cgi/[repository]/[file]?revision=[revision]&view=markup',
            # commit_url='http://cvs.example.com/cgi-bin/viewvc.cgi/[repository]/[file]?r1=[old_revision]&r2=[revision]',

        # git instaweb
            # file_url="http://127.0.0.1:1234/?p=[repository];a=blob;f=[file];h=[revision]"
            # commit_url="http://127.0.0.1:1234/?p=[repository];a=commitdiff;h=[revision]"
        return (base_url, file_url, commit_url, tracker_url)


    def fill_id_cache(self, cursor, column, row):
        """fills the id-cache"""
        value = row[column]
        data = [value]
        extra_column = ""
        extra_data = ""

        # Special case for description column
        if column == "description":
            extra_column = ", hash"
            extra_data = ", %s"
            data.append(len(value))
        elif column == "repository":
            extra_column = ", base_url, file_url, commit_url, tracker_url"
            extra_data = ", %s, %s, %s, %s"
            data.extend(self.guess_repository_urls(row))

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
        self.cache = Cache()
        self.update_database_structure()
        cursor = self.conn.cursor()

        for row in rows:
            for key in self.column_table_mapping:
                self.fill_id_cache(cursor, key, row)

        for row in rows:
            sql = """INSERT IGNORE INTO checkins(type, ci_when, whoid, repositoryid, dirid, fileid, revision, branchid, addedlines, removedlines, descid, stickytag)
                 VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
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
                ""
                ])

        cursor.close()
        self.disconnect()



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

        matchtype = form.getfirst(column+"type", "match")
        operator = '=';
        if (matchtype == "match"):
            operator = '='
        elif (matchtype == "regexp"):
            operator = "REGEXP"
        elif (matchtype == "notregexp"):
            operator = "NOT REGEXP"
        self.sql = self.sql + " AND " + internal_column + " " + operator + " %s"
        self.data.append(value)

    
    def create_where_for_date(self, form):
        """parses the date parameters and adds them to the database query"""

        datetype = form.getfirst("date", "day")
        if (datetype == "all"):
            return
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
            rows = db.fix_encoding_of_result(db.query(self.sql, self.data))
            repositories = db.query_as_double_map("SELECT * FROM repositories", "repository")
            db.disconnect()
            
            result = {
                "config" : self.config['ui'],
                "data" : rows,
                "repositories": repositories
            }

        print(json.dumps(result, default=convert_to_builtin_type))



class PostsaiImporter:
    """Imports commits from a webhook"""

    def __init__(self, config, data):
        self.config = config
        self.data = data

    def split_full_path(self, full_path):
        """splits a full_path into directory and file parts"""

        sep = full_path.rfind("/")
        folder = ""
        if (sep > -1):
            folder = full_path[0:sep]
        file = full_path[sep+1:]
        return folder, file


    def extract_repo_name(self):
        repo = self.data['repository']

        if "full_name" in repo:  # github, sourceforge
            repo_name = repo["full_name"]
        elif "project" in self.data and "path_with_namespace" in self.data["project"]: # gitlab
            repo_name = self.data["project"]["path_with_namespace"]
        else:
            repo_name = repo["name"] # notify-webhook
        return repo_name.strip("/") # sourceforge


    def extract_url(self):
        if "project" in self.data and "web_url" in self.data["project"]: # gitlab
            url = self.data["project"]["web_url"]
        else:
            url = self.data['repository']["url"]
        return url


    def extract_branch(self):
        branch = self.data['ref'][self.data['ref'].rfind("/")+1:]
        if branch == "master":
            return ""
        return branch


    def extract_files(self, commit):
        result = {}
        actionMap = {
            "added" : "Add",
            "copied": "Add",
            "removed" : "Remove",
            "modified" : "Change"
        }
        for change in ("added", "copied", "removed", "modified"):
            if not change in commit:
                continue
            for full_path in commit[change]:
                result[full_path] = actionMap[change]
        return result


    def import_from_webhook(self):
        rows = []

        for commit in self.data['commits']:
            for full_path, change_type in self.extract_files(commit).items():
                folder, file = self.split_full_path(full_path)
                row = {
                    "type" : change_type,
                    "ci_when" : commit['timestamp'],
                    "who" : commit['author']['email'],
                    "url" : self.extract_url(),
                    "repository" : self.extract_repo_name(),
                    "dir" : folder,
                    "file" : file,
                    "revision" : commit['id'],
                    "branch" : self.extract_branch(),
                    "addedlines" : "0",
                    "removedlines" : "0",
                    "description" : commit['message']
                }
                rows.append(row)

        db = PostsaiDB(self.config)
        db.import_data(rows)
        print("Content-Type: text/plain; charset='utf-8'\r")
        print("\r")
        print("Completed")



if __name__ == '__main__':
    if environ.has_key('REQUEST_METHOD') and environ['REQUEST_METHOD'] == "POST":
        PostsaiImporter(vars(config), json.loads(sys.stdin.read())).import_from_webhook()
    else:
        Postsai(vars(config)).process()
