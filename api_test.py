#!/usr/bin/PYTHON

import api
import unittest

class CacheTests(unittest.TestCase):
    """tests for the cache"""

    def cache(self):
        cache = postsai.Cache()
        self.assertIsNone(cache.get("file", "stendhal.java"), "entry not in cache")

        cache.put("file", "stendhal.java", "1")
        self.assertEqual(cache.get("file", "stendhal.java"), "1", "created entry does in cache")


class PostsaiDBTests(unittest.TestCase):
    "test for he db access"

    def test_rewrite(self):
        db = api.PostsaiDB({})

        db.is_viewvc_database = False
        self.assertEquals(
            db.rewrite_sql("SELECT revision FROM checkins WHERE 1=0"),
            "SELECT revision FROM checkins WHERE 1=0",
            "No rewriting on bonsai databases")

        db.is_viewvc_database = True
        self.assertEquals(
            db.rewrite_sql("SELECT revision FROM checkins WHERE 1=0"),
            "SELECT revision FROM commits WHERE 1=0",
            "Rewriting on ViewVC databases")

    def test_fix_encoding_of_result(self):
        data = [["a", u"\u00c4".encode("UTF-8")]]

        res = api.PostsaiDB({}).fix_encoding_of_result(data)

        self.assertEqual(res[0][0], "a", "Normal character is unchanged")
        self.assertEqual(res[0][1], u"\u00c4", "Special character is decoded")



class PostsaiTests(unittest.TestCase):
    "test for the api"

    class FormMock:
        """mock cgi form based on a dictionary"""

        def __init__(self, data):
            self.data = data

        def getfirst(self, key, default=None):
            return self.data[key]

    def test_split_full_path(self):
        postsai = api.Postsai({})
        folder, file = postsai.split_full_path("README.md")
        self.assertEquals(folder, "", "empty folder on README.md")
        self.assertEquals(file, "README.md", "file README.md on README.md")

        folder, file = postsai.split_full_path("")
        self.assertEquals(folder, "", "empty folder on empty")
        self.assertEquals(file, "", "empty file on empty")

        folder, file = postsai.split_full_path("folder/README.md")
        self.assertEquals(folder, "folder", "folder folder on folder/README.md")
        self.assertEquals(file, "README.md", "file README on folder/README.md")



    def test_validate_input(self):
        postsai = api.Postsai({})
        form = self.FormMock({"who" : "postman"})
        self.assertEqual(postsai.validate_input(form), "", "no filter")

        postsai = api.Postsai({"filter" : { "who" : "^cvsscript$" }})
        form = self.FormMock({"who" : "postman"})
        self.assertNotEqual(postsai.validate_input(form), "", "postman is not a permitted user")

        form = self.FormMock({"who" : "cvsscript"})
        self.assertEqual(postsai.validate_input(form), "", "cvsscript is a permitted user")

        form = self.FormMock({"who" : "^cvsscript$"})
        self.assertEqual(postsai.validate_input(form), "", "^cvsscript$ is a permitted user")


    def test_create_where_for_column(self):
        postsai = api.Postsai({})

        postsai.sql = ""
        postsai.data = []
        form = self.FormMock({"file" : "config.py", "filetype" : "",
                              "branch" : "HEAD", "branchtype" : "match",
                              "dir": "webapps.*", "dirtype" : "regexp"})

        postsai.create_where_for_column("file", form, "file")
        self.assertEqual(postsai.sql, " AND file = %s")

        postsai.create_where_for_column("branch", form, "branch")
        self.assertEqual(postsai.sql, " AND file = %s AND branch = %s")

        postsai.create_where_for_column("dir", form, "dir")
        self.assertEqual(postsai.sql, " AND file = %s AND branch = %s AND dir REGEXP %s")

    
    def test_create_where_for_date(self):
        postsai = api.Postsai({})
        postsai.data = []

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "day"}))
        self.assertEqual(postsai.sql, " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 DAY)")

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "week"}))
        self.assertEqual(postsai.sql, " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 WEEK)")

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "month"}))
        self.assertEqual(postsai.sql, " AND ci_when >= DATE_SUB(NOW(),INTERVAL 1 MONTH)")

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "hours", "hours" : "2"}))
        self.assertEqual(postsai.sql, " AND ci_when >= DATE_SUB(NOW(),INTERVAL %s HOUR)")

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "explicit", "mindate" : "2016-02-22", "maxdate" : ""}))
        self.assertEqual(postsai.sql, " AND ci_when >= %s")


if __name__ == '__main__':
    unittest.main()

