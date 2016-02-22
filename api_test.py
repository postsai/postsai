#!/usr/bin/PYTHON

import api
import unittest

class TestStringMethods(unittest.TestCase):
    "test for he api"
    
    class ConfigMock:
        """mock configuration for tests"""

        config_filter = {"who" : "^cvsscript$"}


    class FormMock:
        """mock cgi form based on a dictionary"""

        def __init__(self, dict):
            self.dict = dict

        def getfirst(self, key, default=None):
            return self.dict[key]



    def test_fix_encoding_of_result(self):
        data = [["a", u"\u00c4".encode("UTF-8")]]

        res = api.PostsaiDB(self.ConfigMock()).fix_encoding_of_result(data)

        self.assertEqual(res[0][0], "a", "Normal character is unchanged")
        self.assertEqual(res[0][1], u"\u00c4", "Special character is decoded")


    def test_validate_input(self):
        postsai = api.Postsai(self)
        input = self.FormMock({"who" : "postman"})
        self.assertEqual(postsai.validate_input(input), "", "no filter")

        postsai = api.Postsai(self.ConfigMock())
        input = self.FormMock({"who" : "postman"})
        self.assertNotEqual(postsai.validate_input(input), "", "postman is not a permitted user")

        input = self.FormMock({"who" : "cvsscript"})
        self.assertEqual(postsai.validate_input(input), "", "cvsscript is a permitted user")

        input = self.FormMock({"who" : "^cvsscript$"})
        self.assertEqual(postsai.validate_input(input), "", "^cvsscript$ is a permitted user")


    def test_create_where_for_column(self):
        postsai = api.Postsai(self.ConfigMock())

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
        
        
 

if __name__ == '__main__':
    unittest.main()

