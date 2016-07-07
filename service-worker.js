importScripts('bower_components/sw-toolbox/sw-toolbox.js');

toolbox.router.get(/api.py/, toolbox.networkOnly);
toolbox.router.get(/bower_components/, toolbox.fastest);
toolbox.router.get(/html$/, toolbox.fastest);
toolbox.router.get(/resources/, toolbox.fastest);