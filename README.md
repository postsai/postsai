Postsai &nbsp;&nbsp;&nbsp;&nbsp;[![Travis](https://img.shields.io/travis/postsai/postsai.svg)](https://travis-ci.org/postsai/postsai/) [![Codacy](https://img.shields.io/codacy/b057b8d7eafc41b1a2c4c131b59bcd7c.svg)](https://www.codacy.com/app/arianne/postsai) [![MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/postsai/postsai/blob/master/LICENSE.txt)
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
 
db = {
	"host" : "localhost",
	"user" : "dbuser",
	"password" : "dbpassword",
	"database" : "postsai"
}
```

* Configure commit hook

Integration
-
Postsai can be integrated with ViewVC and various issue trackers, including Github and Bugzilla.

* Add the following configuration to config.py:
``` python
ui = {
	"tracker" : "https://hiszilla.his.de/hiszilla/show_bug.cgi?id=",
	"viewvc" : "https://cvs.his.de/cgi-bin/viewvc.cgi"
}
```

Privacy
-
Postsai supports privacy filters.

A common use case is to prevent queries for changes done by humans. But to allow queries on changes from bot-accounts.

This example limits queries on the who-column to the value "cvsscript".

``` python
filter = {
	"who" : "^cvsscript$"
}
```


<!--
Building
-
zip -r /tmp/postsai-0.1.zip postsai --exclude "*.pyc" --exclude "postsai/config.*" --exclude "postsai/.git/*" --exclude "postsai/.settings/*"

-->