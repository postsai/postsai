#! /usr/bin/python

import cgi
import json
import MySQLdb as mdb
import re
import sys
import datetime
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


    def has(self, entity_type, key):
        """checks whether an item is in the cache"""

        if not entity_type in self.cache:
            return False
        return key in self.cache[entity_type]


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
        self.conn.begin();


    def disconnect(self):
        self.conn.commit()
        self.conn.close()


    def rewrite_sql(self, sql):
        if self.is_viewvc_database:
            sql = sql.replace("checkins", "commits")
        return sql


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

        # GitHub, Gitlab
        if base_url.find("https://github.com/") > -1 or base_url.find("gitlab") > -1:
            commit_url = base_url + "/commit/[revision]"
            file_url = base_url + "/blob/[revision]/[file]"
            tracker_url = base_url + "/issues/$1"

        # SourceForge
        elif base_url.find("://sourceforge.net") > -1:
            if row["revision"].find(".") == -1 and len(row["revision"]) < 30:  # Subversion
                commit_url = "https://sourceforge.net/[repository]/[revision]/"
                file_url = "https://sourceforge.net/[repository]/[revision]/tree/[file]"
            else: # CVS, Git
                commit_url = "https://sourceforge.net/[repository]/ci/[revision]/"
                file_url = "https://sourceforge.net/[repository]/ci/[revision]/tree/[file]"
            icon_url = "https://a.fsdn.com/allura/[repository]/../icon"

        # CVS
        elif row["revision"].find(".") > -1:  # CVS
            commit_url = base + "/[repository]/[file]?r1=[old_revision]&r2=[revision]"
            file_url = base + "/[repository]/[file]?revision=[revision]&view=markup"

        # Git
        else: # git instaweb
            commit_url = base + "/?p=[repository];a=commitdiff;h=[revision]"
            file_url = base + "/?p=[repository];a=blob;f=[file];hb=[revision]"

        return (base_url, file_url, commit_url, tracker_url, icon_url)


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
            extra_column = ", base_url, file_url, commit_url, tracker_url, icon_url"
            extra_data = ", %s, %s, %s, %s, %s"
            data.extend(self.guess_repository_urls(row))
        elif column == "hash":
            extra_column = ", authorid, committerid, co_when, remote_addr, remote_user"
            extra_data = ", %s, %s, %s, %s, %s"
            self.fill_id_cache(cursor, "who", row, row["author"])
            self.fill_id_cache(cursor, "who", row, row["committer"])
            data.extend((self.cache.get("who", row["author"]),
                         self.cache.get("who", row["committer"]),
                         row["co_when"],
                         environ.get("REMOTE_ADDR"),
                         environ.get("REMOTE_USER")))
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


    def import_data(self, rows):
        """Imports data"""

        self.connect()
        self.cache = Cache()
        cursor = self.conn.cursor()

        for row in rows:
            for key in self.column_table_mapping:
                self.fill_id_cache(cursor, key, row, row[key])

        for row in rows:
            sql = """INSERT IGNORE INTO checkins(type, ci_when, whoid, repositoryid, dirid, fileid, revision, branchid, addedlines, removedlines, descid, stickytag, commitid)
                 VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
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
                self.cache.get("hash", row["commitid"])
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
        WHERE 1=1 """

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
        operator = '=';
        if (matchtype == "match"):
            operator = '='
        elif (matchtype == "regexp"):
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
        if internal_column == "description" and matchtype == "search":
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
        return data[9] == pre[9]



    @staticmethod
    def convert_database_row_to_array(row):
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
            repositories = db.query_as_double_map("SELECT * FROM repositories", "repository")
            db.disconnect()

            ui = {}
            if "ui" in vars(config):
                ui = self.config['ui']

            result = {
                "config" : ui,
                "data" : rows,
                "repositories": repositories
            }

        print(json.dumps(result, default=convert_to_builtin_type))



class PostsaiImporter:
    """Imports commits from a webhook"""

    def __init__(self, config, data):
        self.config = config
        self.data = data


    @staticmethod
    def split_full_path(full_path):
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
        """Extracts the branch name, master/HEAD are converted to an empty string."""

        if not "ref" in self.data:
            return ""

        branch = self.data['ref'][self.data['ref'].rfind("/")+1:]
        if branch == "master" or branch == "HEAD":
            return ""
        return branch


    @staticmethod
    def filter_out_folders(files):
        """Sourceforge includes folders in the file list, but we do not want them"""

        result = {}
        for file_to_test, value in files.items():
            for file in files.keys():
                if file.find(file_to_test + "/") == 0:
                    break
            else:
                result[file_to_test] = value
        return result


    @staticmethod
    def extract_files(commit):
        """Extracts a file list from the commit information"""

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


    @staticmethod
    def file_revision(commit, full_path):
        if "revisions" in commit:
            return commit["revisions"][full_path]
        else:
            rev = commit["id"]
            # For Subversion, remove leading r
            if rev[0] == "r":
                rev = rev[1:]
            return rev


    @staticmethod
    def extract_committer(commit):
        if "committer" in commit:
            return commit["committer"]
        else:
            return commit["author"]


    @staticmethod
    def extract_email(author):
        """Use name as replacement for missing or empty email property (Sourceforge Subversion)"""

        if "email" in author and author["email"] != "":
            return author["email"]
        else:
            return author["name"]


    def import_from_webhook(self):
        rows = []
        timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        for commit in self.data['commits']:
            if ("replay" in self.data and self.data["replay"]):
                timestamp = commit["timestamp"]
            for full_path, change_type in self.filter_out_folders(self.extract_files(commit)).items():
                folder, file = self.split_full_path(full_path)
                row = {
                    "type" : change_type,
                    "ci_when" : timestamp,
                    "co_when" : commit["timestamp"],
                    "who" : self.extract_email(commit["author"]),
                    "url" : self.extract_url(),
                    "repository" : self.extract_repo_name(),
                    "dir" : folder,
                    "file" : file,
                    "revision" : self.file_revision(commit, full_path),
                    "branch" : self.extract_branch(),
                    "addedlines" : "0",
                    "removedlines" : "0",
                    "description" : commit["message"],
                    "commitid" : commit["id"],
                    "hash" : commit["id"],
                    "author" : self.extract_email(commit["author"]),
                    "committer" : self.extract_email(self.extract_committer(commit))
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
