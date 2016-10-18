import calendar
import cgi
import json
import MySQLdb as mdb
import re
import sys
import subprocess
import datetime
from os import environ

from db import PostsaiDB


def convert_to_builtin_type(obj):
    """return a string representation for JSON conversation"""

    return str(obj)


class PostsaiCommitViewer:
    """Reads a commit from a repository"""


    def __init__(self, config):
        """Creates a PostsaiCommitViewer instance"""

        self.config = config


    def read_commit(self, form):
        """reads a commmit from the database"""

        db = PostsaiDB(self.config)
        db.connect()
        sql = """SELECT repositories.repository, checkins.ci_when, people.who,
            trim(leading '/' from concat(concat(dirs.dir, '/'), files.file)),
            revision, descs.description, commitids.hash, commitids.co_when, repository_url
            FROM checkins 
            JOIN descs ON checkins.descid = descs.id
            JOIN dirs ON checkins.dirid = dirs.id
            JOIN files ON checkins.fileid = files.id
            JOIN people ON checkins.whoid = people.id
            JOIN repositories ON checkins.repositoryid = repositories.id
            JOIN commitids ON checkins.commitid = commitids.id
            WHERE repositories.repository = %s AND commitids.hash = %s """
        data = [form.getfirst("repository", ""), form.getfirst("commit", "")]
        result = db.query(sql, data)
        db.disconnect()
        return result


    @staticmethod
    def format_commit_header(commit):
        """Extracts the commit meta information"""

        result = {
            "repository": commit[0][0],
            "published": commit[0][1],
            "author": commit[0][2],
            "description": commit[0][5],
            "commit": commit[0][6],
            "timestamp": commit[0][7]
        }
        return result


    @staticmethod
    def calculate_previous_cvs_revision(revision):
        """determine the CVS revision of the previous commit
           which might have been on a parent branch"""
        split = revision.split(".")
        last = split[len(split) - 1]
        if (last == "1" and len(split) > 2):
            split.pop()
            split.pop()
        else:
            split[len(split) - 1] = str(int(last) - 1)
        return ".".join(split)


    @staticmethod
    def dump_commit_diff(commit):
        """dumps the diff generates by invoking CVS to the browser"""

        for file in commit:
            if file[4] == "" or "." not in file[4]:
                sys.stdout.flush()
                print("Index: " + file[3] + " deleted\r")
                sys.stdout.flush()
            else:
                subprocess.call([
                    "cvs",
                    "-d",
                    file[8],
                    "rdiff",
                    "-u",
                    "-r",
                    PostsaiCommitViewer.calculate_previous_cvs_revision(file[4]),
                    "-r",
                    file[4],
                    file[3]])


    def process(self):
        """Returns information about a commit"""

        print("Content-Type: text/plain; charset='utf-8'\r")
        print("Cache-Control: max-age=60\r")
        print("\r")

        form = cgi.FieldStorage()
        commit = self.read_commit(form)

        print(json.dumps(PostsaiCommitViewer.format_commit_header(commit), default=convert_to_builtin_type))
        sys.stdout.flush()
        PostsaiCommitViewer.dump_commit_diff(commit)
