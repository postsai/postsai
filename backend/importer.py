# The MIT License (MIT)
# Copyright (c) 2016-2021 Postsai
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import calendar
import re
import datetime

from backend.db import PostsaiDB


class PostsaiImporter:
    """Imports commits from a webhook"""

    def __init__(self, config, data):
        self.config = config
        self.data = data


    @staticmethod
    def parse_timestamp(t):
        """Parses a timestamp with optional timezone into local time"""

        if len(t) <= 19:
            return t

        parsed = datetime.datetime.strptime(t[0:19],'%Y-%m-%dT%H:%M:%S')
        if t[19]=='+':
            parsed -= datetime.timedelta(hours=int(t[20:22]))
        elif t[19]=='-':
            parsed += datetime.timedelta(hours=int(t[20:22]))
        return datetime.datetime.fromtimestamp(calendar.timegm(parsed.timetuple())).isoformat()



    def check_permission(self, repo_name):
        """checks writes write permissions"""

        if not "get_write_permission_pattern" in self.config:
            return True
        regex = self.config["get_write_permission_pattern"]()
        return not re.match(regex, repo_name) == None


    @staticmethod
    def split_full_path(full_path):
        """splits a full_path into directory and file parts"""

        sep = full_path.rfind("/")
        folder = ""
        if (sep > -1):
            folder = full_path[0:sep]
        file = full_path[sep+1:]
        return folder, file


    def call_normalize_repository_name(self, repo):
        """let the configuration overwrite repository name"""

        if not "normalize_repository_name" in self.config:
            return repo
        return self.config["normalize_repository_name"](repo)


    def extract_repo_name(self):
        """extracts the name of the repository"""

        repo = self.data['repository']

        if "full_name" in repo:  # github, sourceforge
            repo_name = repo["full_name"]
        elif "project" in self.data and "path_with_namespace" in self.data["project"]: # gitlab
            repo_name = self.data["project"]["path_with_namespace"]
        else:
            repo_name = repo["name"] # notify-webhook
        repo_name = repo_name.strip("/") # sourceforge
        return self.call_normalize_repository_name(repo_name)


    def extract_repo_url(self):
        """extracts the url to the repository itself (not the web interface)"""

        repo = self.data['repository']
        repository_url = ""

        if "clone_url" in repo:  # github
            repository_url = repo["clone_url"]
        elif "git_ssh_url" in repo: # gitlab
            repository_url = repo["git_ssh_url"]
        elif "url" in repo: # sourceforge, notify-cvs-webhook
            repository_url = repo["url"]
        return repository_url


    def extract_repo_forked_from(self):
        """extracts the name of the repository this repository was forked from. May be 'upstream', if the source repository is unknown."""

        repo = self.data['repository']
        forked_from = ""

        if "forked_from" in repo:  # none, but would be nice
            forked_from = repo["forked_from"]
        elif "forked" in repo: # github
            if repo["forked"]:
                forked_from = "upstream"
        return forked_from


    def extract_url(self):
        """extracts the url to the web interface"""

        if "project" in self.data and "web_url" in self.data["project"]: # gitlab
            url = self.data["project"]["web_url"]
        elif "home_url" in self.data['repository']:
            url = self.data['repository']["home_url"]
        else:
            url = self.data['repository']["url"]
        return url


    def extract_branch(self):
        """Extracts the branch name, master/HEAD are converted to an empty string."""

        if not "ref" in self.data:
            return ""

        # skip "refs/heads/" prefix
        ref = self.data['ref']
        idx = ref.find("/", ref.find("/") + 1)
        branch = ref[idx+1:]
        if branch == "master" or branch == "HEAD":
            return ""
        return branch


    @staticmethod
    def filter_out_folders(files):
        """Sourceforge includes folders in the file list, but we do not want them"""

        result = {}
        for file_to_test, value in list(files.items()):
            for file in list(files.keys()):
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
        """extracts the file version (mostly interesting for CVS)"""

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
        """extracts the element of the commiter, falling back to the author"""

        if "committer" in commit:
            return commit["committer"]
        else:
            return commit["author"]


    @staticmethod
    def extract_email(author):
        """Use name as replacement for missing or empty email property (Sourceforge Subversion)"""

        if "email" in author and author["email"] != "":
            return author["email"].lower()
        elif "name" in author:
            return author["name"].lower()
        return ""


    def extract_sender_addr(self):
        """extracts the client address of the push"""

        if "sender" in self.data:
            if "addr" in self.data["sender"]:
                return self.data["sender"]["addr"]
        return ""


    def extract_sender_user(self):
        """extracts the account of the user doing the push"""

        if "sender" in self.data:
            if "login" in self.data["sender"]:
                return self.data["sender"]["login"]
        if "user_email" in self.data:
            return self.data["user_email"]
        if "user_id" in self.data:
            return self.data["user_id"]
        if "user_name" in self.data:
            return self.data["user_name"]

        return ""


    def parse_data(self):
        """parse webhook data"""

        head = {
            "sender_addr": self.extract_sender_addr(),
            "sender_user": self.extract_sender_user()
        }

        rows = []
        timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        repo_name = self.extract_repo_name()

        for commit in self.data['commits']:
            if ("replay" in self.data and self.data["replay"]):
                timestamp = self.parse_timestamp(commit["timestamp"])
            for full_path, change_type in list(self.filter_out_folders(self.extract_files(commit)).items()):
                folder, file = self.split_full_path(full_path)
                row = {
                    "type" : change_type,
                    "ci_when" : timestamp,
                    "co_when" : self.parse_timestamp(commit["timestamp"]),
                    "who" : self.extract_email(commit["author"]),
                    "url" : self.extract_url(),
                    "repository" : repo_name,
                    "repository_url" : self.extract_repo_url(),
                    "forked_from" : self.extract_repo_forked_from(),
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

        return head, rows


    def import_from_webhook(self):
        """Import this webhook invokation into the database"""

        repo_name = self.extract_repo_name()
        if not self.check_permission(repo_name):
            print("Status: 403 Forbidden\r")
            print("Content-Type: text/html; charset='utf-8'\r")
            print("\r")
            print("<html><body>Missing permission</body></html>")

        print("Content-Type: text/plain; charset='utf-8'\r")
        print("\r")

        head, rows = self.parse_data()
        db = PostsaiDB(self.config)
        db.import_data(head, rows)
        print("Completed")
