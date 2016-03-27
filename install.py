#!/usr/bin/python

import sys
import api
import warnings

class PostsaiInstaller:
    """Installer for Postsai"""

    @staticmethod
    def print_config_help_and_exit():
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


    def has_index(self, table, name):
        """checks whether the specified index exists on the specified table"""

        sql = "SHOW INDEX FROM " + table + " WHERE key_name = %s"
        data = [name]
        rows = self.db.query(self.db.rewrite_sql(sql), data)
        return len(rows) > 0


    def convert_to_innodb(self, db):
        """Converts all database tables to InnoDB"""

        sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND ENGINE = 'MyISAM'"
        data = [self.config["db"]["database"]]
        rows = db.query(sql, data);
        data = []
        for row in rows:
            db.query("ALTER TABLE " + row[0] + " ENGINE=INNODB", data);


    def convert_to_utf8(self, db):
        """Converts all database tables to UTF-8"""
        query = """SELECT table_name
FROM information_schema.tables, information_schema.collation_character_set_applicability
WHERE collation_character_set_applicability.collation_name = tables.table_collation
AND table_schema = %s AND character_set_name != 'utf8'"""

        data = [self.config["db"]["database"]]
        tables = db.query(query, data);
        for table in tables:
            db.query("ALTER TABLE " + table[0] + "  CONVERT TO CHARSET 'UTF8' COLLATE utf8_bin", []);


    def update_database_structure(self):
        structure = """
ALTER DATABASE """ + self.config["db"]["database"] + """ CHARSET 'UTF8';
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
  `commitid` mediumint(9),
  PRIMARY KEY(`id`),
  UNIQUE KEY `domainid` (`repositoryid`, `branchid`, `dirid`, `fileid`, `revision`),
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
  `dir` varchar(254) DEFAULT NULL,
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
);
CREATE TABLE IF NOT EXISTS `commitids` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `hash` varchar(60),
  `co_when` datetime NOT NULL,
  `authorid` mediumint(9) NOT NULL,
  `committerid` mediumint(9) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hash` (`hash`)
)  
        """
        print("OK: Starting database structure check and update")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for sql in structure.split(";"):
                self.db.query(self.db.rewrite_sql(sql), [])

        self.convert_to_innodb(self.db)
        self.convert_to_utf8(self.db)
        self.db.update_database_structure()

        if self.has_index("checkins", "repository"):
            self.db.query(self.db.rewrite_sql("ALTER TABLE checkins DROP INDEX repositoryid"), [])

        if not self.has_index("checkins", "domainid"):
            self.db.query(self.db.rewrite_sql("ALTER TABLE checkins ADD UNIQUE KEY `domainid` (`repositoryid`, `branchid`, `dirid`, `fileid`, `revision`)"), [])

        if not self.has_index("descs", "i_description"):
            try:
                self.db.query("CREATE FULLTEXT INDEX `i_description` ON `descs` (`description`)", [])
            except:
                print("WARN: Could not create fulltext index. MySQL version >= 5.6 required.")

        print("OK: Completed database structure check and update")


    def main(self):
        self.import_config()
        self.check_db_config()
        self.connect()
        self.update_database_structure()



if __name__ == '__main__':
    PostsaiInstaller().main()
