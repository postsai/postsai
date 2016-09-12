importScripts('node_modules/sw-toolbox/sw-toolbox.js');

toolbox.router.get(/api.py/, toolbox.networkOnly);
toolbox.router.get(/node_modules/, toolbox.fastest);
toolbox.router.get(/html$/, toolbox.fastest);
toolbox.router.get(/resources/, toolbox.fastest);