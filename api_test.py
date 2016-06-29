#!/usr/bin/PYTHON

import api
import unittest

class CacheTests(unittest.TestCase):
    """tests for the cache"""

    def test_cache(self):
        cache = api.Cache()
        self.assertIsNone(cache.get("file", "stendhal.java"), "entry not in cache")

        cache.put("file", "stendhal.java", "1")
        self.assertEqual(cache.get("file", "stendhal.java"), "1", "created entry in cache")

        cache.put("file", "stendhal.java", "2")
        self.assertEqual(cache.get("file", "stendhal.java"), "2", "update entry does in cache")

        self.assertTrue(cache.has("file", "stendhal.java"), "has")
        self.assertFalse(cache.has("file", "none"), "has not")
        self.assertFalse(cache.has("dir", "stendhal.java"), "has not group")



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
        self.assertEqual(res[0][1], u"\u00c4".encode("UTF-8"), "Special character is decoded")


    def test_guess_repository_urls(self):
        db = api.PostsaiDB({})

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://github.com/postsai/postsai",
                "repository": "postsai/postsai"
            })[2],
            "https://github.com/postsai/postsai/commit/[revision]",
            "Github")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://sourceforge.net",
                "repository" : "/p/arianne/stendhal/",
                "revision" : "37ab54349f9ee12c4bfc6236cc2ce61ed24692ec"
            })[2],
            "https://sourceforge.net/[repository]/ci/[revision]/",
            "SourceForge Git")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://sourceforge.net",
                "repository" : "/p/testsf2/svn/",
                "revision" : "r4"
            })[2],
            "https://sourceforge.net/[repository]/[revision]/",
            "SourceForge Subversion")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "http://localhost/cgi-bin/viewvc.cgi",
                "repository" : "myrepo",
                "revision" : "1.1"
            })[2],
            "http://localhost/cgi-bin/viewvc.cgi/[repository]/[file]?r1=[old_revision]&r2=[revision]",
            "CVS")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "http://localhost",
                "repository" : "myrepo",
                "revision" : "37ab54349f9ee12c4bfc6236cc2ce61ed24692ec"
            })[2],
            "http://localhost/?p=[repository];a=commitdiff;h=[revision]",
            "Git")


class PostsaiTests(unittest.TestCase):
    "test for the api"

    class FormMock:
        """mock cgi form based on a dictionary"""

        def __init__(self, data):
            self.data = data

        def getfirst(self, key, default=None):
            return self.data.get(key, default)


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

        form = self.FormMock({})
        self.assertEqual(postsai.validate_input(form), "", "parameter is not present")


    def test_create_where_for_column(self):
        postsai = api.Postsai({})

        postsai.sql = ""
        postsai.data = []
        form = self.FormMock({"file" : "config.py", "filetype" : "",
                              "branch" : "HEAD", "branchtype" : "match",
                              "dir": "webapps.*", "dirtype" : "regexp",
                              "repository" : "stendhal", "repositorytype" : "notregexp",
                              "description" : "bla", "descriptiontype" : "search"})

        postsai.create_where_for_column("who", form, "who")
        self.assertEqual(postsai.sql, "", "undefined parameter")

        postsai.create_where_for_column("file", form, "file")
        self.assertEqual(postsai.sql, " AND file = %s", "file with empty match type")

        postsai.create_where_for_column("branch", form, "branch")
        self.assertEqual(postsai.sql, " AND file = %s AND branch = %s", "branch with match")

        postsai.create_where_for_column("dir", form, "dir")
        self.assertEqual(postsai.sql, " AND file = %s AND branch = %s AND dir REGEXP %s", "dir with regexp")

        postsai.sql = ""
        postsai.create_where_for_column("repository", form, "repository")
        self.assertEqual(postsai.sql, " AND repository NOT REGEXP %s", "repository with not regexp")

        postsai.sql = ""
        postsai.create_where_for_column("description", form, "description")
        self.assertEqual(postsai.sql, " AND MATCH (description) AGAINST (%s)", "description matching")


    def test_create_where_for_date(self):
        postsai = api.Postsai({})
        postsai.data = []

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "none"}))
        self.assertEqual(postsai.sql, " AND 1 = 0")

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

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "explicit", "mindate" : "", "maxdate" : "2016-02-22"}))
        self.assertEqual(postsai.sql, " AND ci_when <= %s")

        postsai.sql = ""
        postsai.create_where_for_date(self.FormMock({"date" : "invalid21345"}))
        self.assertEqual(postsai.sql, "")



class PostsaiImporterTests(unittest.TestCase):
    "test for the importer"


    def test_split_full_path(self):
        postsai = api.PostsaiImporter({}, {})
        folder, file = postsai.split_full_path("README.md")
        self.assertEquals(folder, "", "empty folder on README.md")
        self.assertEquals(file, "README.md", "file README.md on README.md")

        folder, file = postsai.split_full_path("")
        self.assertEquals(folder, "", "empty folder on empty")
        self.assertEquals(file, "", "empty file on empty")

        folder, file = postsai.split_full_path("folder/README.md")
        self.assertEquals(folder, "folder", "folder folder on folder/README.md")
        self.assertEquals(file, "README.md", "file README on folder/README.md")


    def test_filter_out_folders(self):
        postsai = api.PostsaiImporter({}, {})
        res = postsai.filter_out_folders({"content" : "change", "content/game" : "change", "content/game/sourcelog.php" : "change" })
        self.assertIn("content/game/sourcelog.php", res, "file remained in list")
        self.assertNotIn("content", res, "folder was removed from list")
        self.assertNotIn("content/game", res, "folder was removed from list")


    def test_file_revision(self):
        postsai = api.PostsaiImporter({}, {})
        self.assertEqual(postsai.file_revision({"id" : "r2"}, {}), "2", "Subversion version without r")
        self.assertEqual(postsai.file_revision({"id" : "eef37d923574175c5606d04af19793f63c056f82"}, {}), "eef37d923574175c5606d04af19793f63c056f82", "Git revision")
        self.assertEqual(postsai.file_revision({"revisions" : {"bla" : "1.1"}}, "bla"), "1.1", "CVS file revision")


    def test_extract_branch(self):
        importer = api.PostsaiImporter({}, {})
        self.assertEqual(importer.extract_branch(), "", "no branch")

        importer.data["ref"] = "HEAD"
        self.assertEqual(importer.extract_branch(), "", "HEAD branch")

        importer.data["ref"] = "refs/heads/master"
        self.assertEqual(importer.extract_branch(), "", "master branch")

        importer.data["ref"] = "refs/heads/dev"
        self.assertEqual(importer.extract_branch(), "dev", "master branch")


    def test_extract_repo_name(self):
        importer = api.PostsaiImporter({}, {"repository" : { "full_name" : "arianne/stendhal"}})
        self.assertEqual(importer.extract_repo_name(), "arianne/stendhal", "GitHub repository")

        importer = api.PostsaiImporter({}, {"repository" : { "full_name" : "/p/arianne/stendhal-website/"}})
        self.assertEqual(importer.extract_repo_name(), "p/arianne/stendhal-website", "SourceForge repository")

        importer = api.PostsaiImporter({}, {"project" : { "path_with_namespace" : "cs.sys/cs.sys.portal"},
                                            "repository": { "name": "cs.sys.portal"}})
        self.assertEqual(importer.extract_repo_name(), "cs.sys/cs.sys.portal", "Gitlab repository")

        importer = api.PostsaiImporter({}, {"repository" : { "name" : "gittest"}})
        self.assertEqual(importer.extract_repo_name(), "gittest", "Git repository")


    def test_extract_url(self):
        importer = api.PostsaiImporter({}, {"repository" : { "url" : "https://github.com/arianne/stendhal"}})
        self.assertEqual(importer.extract_url(), "https://github.com/arianne/stendhal", "GitHub repository")

        importer.data = {"project": { "web_url":"https://example.com/arianne/stendhal" }}
        self.assertEqual(importer.extract_url(), "https://example.com/arianne/stendhal", "Gitlab repository")



if __name__ == '__main__':
    unittest.main()
