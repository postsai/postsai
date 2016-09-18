#!/usr/bin/PYTHON

import api
import unittest

def get_permission_pattern():
    return "^test$"

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


    def test_guess_repository_urls(self):
        db = api.PostsaiDB({})

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://github.com/postsai/postsai",
                "repository": "postsai/postsai",
                "repository_url": ""
            })[3],
            "https://github.com/postsai/postsai/commit/[commit]",
            "Github")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://sourceforge.net",
                "repository" : "/p/arianne/stendhal/",
                "repository_url": "",
                "revision" : "37ab54349f9ee12c4bfc6236cc2ce61ed24692ec"
            })[3],
            "https://sourceforge.net/[repository]/ci/[commit]/",
            "SourceForge Git")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "https://sourceforge.net",
                "repository" : "/p/testsf2/svn/",
                "repository_url": "",
                "revision" : "r4"
            })[3],
            "https://sourceforge.net/[repository]/[commit]/",
            "SourceForge Subversion")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "http://localhost/cgi-bin/viewvc.cgi",
                "repository" : "myrepo",
                "repository_url": "",
                "revision" : "1.1"
            })[3],
            "commit.html?repository=[repository]&commit=[commit]",
            "CVS")

        self.assertEqual(
            db.guess_repository_urls({
                "url" : "http://localhost",
                "repository" : "myrepo",
                "repository_url": "",
                "revision" : "37ab54349f9ee12c4bfc6236cc2ce61ed24692ec"
            })[3],
            "http://localhost/?p=[repository];a=commitdiff;h=[commit]",
            "Git")


    def test_extra_data_for_key_tables(self):
        """test for extra_data_for_key_tables"""

        db = api.PostsaiDB({})
        row = {"repository": "repo", "url": "http://example.com", "repository_url": "", "revision": "1.1"}

        self.assertEqual(
            db.extra_data_for_key_tables(None, "column", row, "value"),
            (["value"], "", ""),
            "No extra data for unknown column")

        self.assertEqual(
            db.extra_data_for_key_tables(None, "description", row, "value"),
            (["value", 5], ", hash", ", %s"),
            "Extra data for description column")

        self.assertEqual(
            db.extra_data_for_key_tables(None, "repository", row, "value"),
            (["value", "http://example.com/repo", "", "http://example.com/[repository]/[file]?revision=[revision]&view=markup", "commit.html?repository=[repository]&commit=[commit]", "", ""],
             ", base_url, repository_url, file_url, commit_url, tracker_url, icon_url",
             ", %s, %s, %s, %s, %s, %s"),
            "Extra data for repository column")



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


    def test_get_read_permission_pattern(self):
        postsai = api.Postsai({})
        self.assertEqual(postsai.get_read_permission_pattern(), ".*", "no read permission function")

        postsai = api.Postsai({"get_read_permission_pattern" : get_permission_pattern})
        self.assertEqual(postsai.get_read_permission_pattern(), "^test$", "read permission function defined")


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


    def test_create_query(self):
        postsai = api.Postsai({})
        postsai.create_query(self.FormMock({"limit" : "10"}))
        self.assertTrue("LIMIT 10" in postsai.sql, "Limit")


    def test_extract_commits(self):
        self.assertEqual(api.Postsai.extract_commits([]), [], "empty result")
        commit1 = ["", "", "", "file 1", "1.1", "", "", "", "", "commitid"]
        commit2 = ["", "", "", "file 2", "1.2", "", "", "", "", "commitid"]
        commit3 = ["", "", "", "file 3", "1.3", "", "", "", "", "commitid 2"]

        self.assertEqual(
            api.Postsai.extract_commits([commit1]),
            [["", "", "", ["file 1"], ["1.1"], "", "", "", "", "commitid"]],
            "one row")

        self.assertEqual(
            api.Postsai.extract_commits([commit1, commit2]),
            [["", "", "", ["file 1", "file 2"], ["1.1", "1.2"], "", "", "", "", "commitid"]],
            "one commit")

        self.assertEqual(
            api.Postsai.extract_commits([commit1, commit2, commit3]),
            [["", "", "", ["file 1", "file 2"], ["1.1", "1.2"], "", "", "", "", "commitid"],
             ["", "", "", ["file 3"], ["1.3"], "", "", "", "", "commitid 2"]],
            "two commits")



class PostsaiCommitViewerTest(unittest.TestCase):

    def test_calculate_previous_cvs_revision(self):
        self.assertEqual(api.PostsaiCommitViewer.calculate_previous_cvs_revision("1.2"), "1.1")
        self.assertEqual(api.PostsaiCommitViewer.calculate_previous_cvs_revision("1.3.2.4"), "1.3.2.3")
        self.assertEqual(api.PostsaiCommitViewer.calculate_previous_cvs_revision("1.3.2.1"), "1.3")
        self.assertEqual(api.PostsaiCommitViewer.calculate_previous_cvs_revision("1.1"),     "1.0")



class PostsaiImporterTests(unittest.TestCase):
    "test for the importer"


    def test_parse_timestamp(self):
        postsai = api.PostsaiImporter({}, {})

        a = postsai.parse_timestamp("2015-05-05T19:40:15+04:00")
        b = postsai.parse_timestamp("2015-05-05T19:40:15")
        c = postsai.parse_timestamp("2015-05-05T19:40:15-04:00")

        self.assertLess(a, b)
        self.assertLess(b, c)


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


    def test_extract_repo_url(self):
        importer = api.PostsaiImporter({}, {"repository" : {}})
        self.assertEqual(importer.extract_repo_url(), "", "No repository url")

        importer = api.PostsaiImporter({}, {"repository" : { "clone_url": "https://github.com/arianne/stendhal.git"}})
        self.assertEqual(importer.extract_repo_url(), "https://github.com/arianne/stendhal.git", "GitHub repository")

        importer = api.PostsaiImporter({}, {"repository" : { "git_ssh_url" : "git@example.com:cs.sys/cs.sys.portal.git"}})
        self.assertEqual(importer.extract_repo_url(), "git@example.com:cs.sys/cs.sys.portal.git", "Gitlab repository")

        importer = api.PostsaiImporter({}, {"repository" : { "url" : ":pserver:anonymous:@cvs.example.com/srv/cvs/repository"}})
        self.assertEqual(importer.extract_repo_url(), ":pserver:anonymous:@cvs.example.com/srv/cvs/repository", "CVS repository")


    def test_extract_url(self):
        importer = api.PostsaiImporter({}, {"repository" : { "url" : "https://github.com/arianne/stendhal"}})
        self.assertEqual(importer.extract_url(), "https://github.com/arianne/stendhal", "GitHub repository")

        importer = api.PostsaiImporter({}, {"repository" : { "home_url" : "https://cvs.example.com/viewvc"}})
        self.assertEqual(importer.extract_url(), "https://cvs.example.com/viewvc", "CVS")

        importer.data = {"project": { "web_url":"https://example.com/arianne/stendhal" }}
        self.assertEqual(importer.extract_url(), "https://example.com/arianne/stendhal", "Gitlab repository")


    def test_extract_files(self):
        self.assertEqual(api.PostsaiImporter.extract_files(
            {
                "added": [],
                "removed": [],
                "modified": ["README.md"]
            }),
            {'README.md': 'Change'})


    def test_check_permission(self):
        importer = api.PostsaiImporter({}, {})
        self.assertTrue(importer.check_permission("something"), "no permission pattern defined")

        importer = api.PostsaiImporter({"get_write_permission_pattern" : get_permission_pattern}, {})
        self.assertTrue(importer.check_permission("test"), "matching permission pattern defined")
        self.assertFalse(importer.check_permission("something"), "not matching permission defined")


    def test_extract_email(self):
        importer = api.PostsaiImporter({}, {})
        self.assertEqual(importer.extract_email({"email": "Name@example.com"}), "name@example.com")
        self.assertEqual(importer.extract_email({"email": "", "name": "bla"}), "bla")
        self.assertEqual(importer.extract_email({"name": "Name@example.com"}), "name@example.com")
        self.assertEqual(importer.extract_email({}), "")


    def test_extract_sender_user(self):
        importer = api.PostsaiImporter({}, {"user_email": "me@example.com"})
        self.assertEqual(importer.extract_sender_user(), "me@example.com")

        importer = api.PostsaiImporter({}, {"user_id": "12345"})
        self.assertEqual(importer.extract_sender_user(), "12345")

        importer = api.PostsaiImporter({}, {"user_name": "username"})
        self.assertEqual(importer.extract_sender_user(), "username")

        importer = api.PostsaiImporter({}, {"sender": {}})
        self.assertEqual(importer.extract_sender_user(), "")



    def test_parse_data(self):
        importer = api.PostsaiImporter({},
            {
                "ref": "refs/heads/HEAD",
                "after": "10056E40FB51177B8D0",
                "commits": [
                    {
                        "id": "10056E40FB51177B8D0",
                        "distinct": "true",
                        "message": "this is the commit message",
                        "timestamp": "2016-03-12T13:46:45",
                        "author": {
                           "name": "myself",
                            "email": "myself@example.com",
                            "username": "myself"
                        },
                        "committer": {
                            "name": "myself",
                            "email": "myself@example.com",
                            "username": "myself"
                        },
                        "added": [],
                        "removed": [],
                        "modified": ["mymodule/myfile"],
                        "revisions": {
                            "mymodule/myfile": "1.9"
                        }
                    }
                ],
                "head_commit": {
                    "id": "10056E40FB51177B8D0",
                    "distinct": "true",
                    "message": "this is the commit message",
                    "timestamp": "2016-03-12T13:46:45",
                    "author": {
                        "name": "myself",
                        "email": "myself@example.com",
                        "username": "myself"
                    },
                    "committer": {
                        "name": "myself",
                        "email": "myself@example.com",
                        "username": "myself"
                    },
                    "added": [],
                    "removed": [],
                    "modified": ["mymodule/myfile"],
                    "revisions": {
                        "mymodule/myfile": "1.9"
                    }
                },
                "repository": {
                     "name": "local",
                     "full_name": "local",
                     "home_url": "https://cvs.example.com/viewvc/",
                     "url": ":pserver:username:password@cvs.example.com/repository"
                },
                "sender": {
                    "login": "username",
                    "addr": "127.0.0.1"
                }
            })
        head, rows = importer.parse_data()
        self.assertEqual(head["sender_user"], "username")
        self.assertEqual(head["sender_addr"], "127.0.0.1")
        self.assertEqual(len(rows), 1)



if __name__ == '__main__':
    unittest.main()
