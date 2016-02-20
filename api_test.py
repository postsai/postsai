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

 

if __name__ == '__main__':
    unittest.main()

