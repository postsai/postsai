#!/usr/bin/python

import sys
import api
import warnings

class PostsaiInstaller:

    def print_config_help_and_exit(self):
        help_config_file = """
    Please create a file called config.py with this content an run install.py again: 

    db = {
        "host" : "localhost",
        "user" : "postsaiuser",
        "password" : "postsaipassword",
        "database" : "postsaidb"
    }
    """
        print(help_config_file)
        sys.exit(1)


    def import_config(self):
        try:
            import config
        except ImportError:
            self.print_config_help_and_exit()

        print("OK: Found config file")
        self.config = vars(config)


    def check_db_config(self):
        if not "db" in self.config:
            print("ERR: Missing parameter \"db\" in config file.")
            self.print_config_help_and_exit()

        for param in ["host", "user", "password", "database"]:
            if not param in self.config["db"]:
                print("ERR: Missing parameter in \"db\" section of config file.")
                self.print_config_help_and_exit()
        print "OK: Found database configuration"


    def connect(self):
        try:
            self.db = api.PostsaiDB(self.config)
            self.db.connect()
            print("OK: Connected to database")
        except Exception as err:
            print("ERR: Failed to connect to database \"" + self.config["db"]["database"] + "\":")
            print(err)
            sys.exit(1)


    def update_database_structure(self):
        structure = """
CREATE TABLE IF NOT EXISTS `branches` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `branch` varchar(200),
  PRIMARY KEY (`id`), UNIQUE KEY `branch` (`branch`)
);
CREATE TABLE IF NOT EXISTS `checkins` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `type` enum('Change','Add','Remove') DEFAULT NULL,
  `ci_when` datetime NOT NULL,
  `whoid` mediumint(9) NOT NULL,
  `repositoryid` mediumint(9) NOT NULL,
  `dirid` mediumint(9) NOT NULL,
  `fileid` mediumint(9) NOT NULL,
  `revision` char(50) DEFAULT NULL,
  `stickytag` varchar(255) NOT NULL,
  `branchid` mediumint(9) NOT NULL,
  `addedlines` int(11) NOT NULL,
  `removedlines` int(11) NOT NULL,
  `descid` mediumint(9) NOT NULL,
  PRIMARY KEY(`id`),
  UNIQUE KEY `repositoryid` (`repositoryid`,`dirid`,`fileid`,`revision`),
  KEY `ci_when` (`ci_when`),
  KEY `whoid` (`whoid`),
  KEY `repositoryid_2` (`repositoryid`),
  KEY `dirid` (`dirid`),
  KEY `fileid` (`fileid`),
  KEY `branchid` (`branchid`),
  KEY `descid` (`descid`)
);
CREATE TABLE IF NOT EXISTS `descs` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `description` text,
  `hash` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `hash` (`hash`)
);
CREATE TABLE IF NOT EXISTS `dirs` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `dir` varchar(700) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dir` (`dir`)
);
CREATE TABLE IF NOT EXISTS `files` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `file` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `file` (`file`)
);
CREATE TABLE IF NOT EXISTS `people` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `who` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `who` (`who`)
);
CREATE TABLE IF NOT EXISTS `repositories` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `repository` varchar(64) NOT NULL,
  `base_url` varchar(255) DEFAULT NULL,
  `file_url` varchar(255) DEFAULT NULL,
  `commit_url` varchar(255) DEFAULT NULL,
  `tracker_url` varchar(255) DEFAULT NULL,
  `icon_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `repository` (`repository`)
);
CREATE TABLE IF NOT EXISTS `tags` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `repositoryid` mediumint(9) NOT NULL,
  `branchid` mediumint(9) NOT NULL,
  `dirid` mediumint(9) NOT NULL,
  `fileid` mediumint(9) NOT NULL,
  `revision` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `repositoryid` (`repositoryid`,`dirid`,`fileid`,`branchid`,`revision`),
  KEY `repositoryid_2` (`repositoryid`),
  KEY `dirid` (`dirid`),
  KEY `fileid` (`fileid`),
  KEY `branchid` (`branchid`)
)
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for sql in structure.split(";"):
                self.db.query(sql, [])
        print("OK: Database structure check & update")

    def print_apache_help(self):
        # TODO
        pass


    def main(self):
        self.import_config()
        self.check_db_config()
        self.connect()
        self.update_database_structure()
        self.print_apache_help()



if __name__ == '__main__':
    PostsaiInstaller().main()