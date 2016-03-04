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
Postsai integrates with various hosted and local repositories:

- GitHub, Gitlab and SourceForge
  - Just add a Webhook to https://example.com/postsai/api.py and you are done.
- Self hosted Git repositories (including Gitolite)
  - Use [notify-webhook](https://github.com/youyongsong/notify-webhook) to setup a webhook with the following configuration<br>webhookurl=https://example.com/postsai/api.py<br> webhook-contenttype=application/json
  - Edit the database table "repositories" to configure links. For git instaweb use: <br>file_url=http://example.com/?p=[repository];a=blob;f=[file];h=[revision]<br>commit_url=http://example.com/?p=[repository];a=commitdiff;h=[revision]
- CVS
  - Setup [ViewVC](http://www.viewvc.org/) with database suport (for example via apt-get install viewvc viewvc-query) and use the same database for Postsai
  - Edit the database table "repositories" to configure links.<br>file_url=http://cvs.example.com/cgi-bin/viewvc.cgi/[repository]/[file]?revision=[revision]&view=markup<br>commit_url=http://cvs.example.com/cgi-bin/viewvc.cgi/[repository]/[file]?r1=[old_revision]&r2=[revision]

   
A global issue tracker is supported as fallback by adding the following configuration to config.py
``` python
ui = {
	"tracker" : "https://hiszilla.his.de/hiszilla/show_bug.cgi?id=",
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

By default the full email address of the author is displayed without profile icon. Both settings can be configured independently:

``` python
ui = {
    "avatar" : "https://gravatar.com",
    "trim_email" : True
}
```

<!--
Building
-
zip -r /tmp/postsai-0.1.zip postsai --exclude "*.pyc" --exclude "postsai/config.*" --exclude "postsai/.git/*" --exclude "postsai/.settings/*"

-->