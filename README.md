Postsai &nbsp;&nbsp;&nbsp;&nbsp;[![Travis](https://img.shields.io/travis/postsai/postsai.svg)](https://travis-ci.org/postsai/postsai/) [![Code Climate](https://img.shields.io/codeclimate/github/postsai/postsai.svg)](https://codeclimate.com/github/postsai/postsai) [![MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/postsai/postsai/blob/master/LICENSE.txt)
-------

Postsai is a commit database

Installation
------------

* Install dependencies

``` bash
apt-get install python python-mysqldb
```

* Create a postsai database in MySQL.
* Unzip postsai to your web server directory
* Create a file config.py with the following content:

``` python
#!/usr/bin/python
 
config_db_host = "localhost"
config_db_user = "dbuser"
config_db_password = "dbpassword"
config_db_database = "postsai"
```

* Configure commit hook

Integration
-
Postsai can be integreated with ViewVC and various issue trackers, including Github and Bugzilla.

* Create a file config.js with the following content:
``` javascript
tracker = "https://hiszilla.his.de/hiszilla/show_bug.cgi?id="
viewvc = "https://cvs.his.de/cgi-bin/viewvc.cgi";
```

Privacy
-
Postsai supports privacy filters.

A common use case is to prevent queries for changes done by humans. But to allow queries on changes from bot-accounts.

This example limits queries on the who-column to the value "cvsscript".

``` python
config_filter = {"who" : "^cvsscript$"}
```


<!--
Building
-
zip -r /tmp/postsai-0.1.zip postsai --exclude "*.pyc" --exclude "postsai/config.*" --exclude "postsai/.git/*" --exclude "postsai/.settings/*"

-->