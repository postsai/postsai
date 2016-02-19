Postsai
-------

Postsai is a commit database

Installation
------------

``` bash
apt-get install python python-mysqldb
```

* Create a postsai database in MySQL.
* unzip postsai to your web server

Create a file config.py with the following content:

``` python
#!/usr/bin/python
 
config_db_host = "localhost"
config_db_user = "dbuser"
config_db_password = "dbpassword"
config_db_database = "postsai"
```

* configure commit hook