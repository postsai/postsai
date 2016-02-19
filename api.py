#! /usr/bin/python

import MySQLdb as mdb
import config

def convert_to_builtin_type(obj):
    return str(obj)

class Postsai:
    
    def query(self):
        """Executes the database query and prints the result"""

        conn = mdb.connect(config.config_db_host, config.config_db_user, config.config_db_password, config.config_db_database)
        cursor = conn.cursor()
        cursor.execute(self.sql, self.data)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()
        return rows
