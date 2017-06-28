// import the standard service worker toolbox
importScripts('node_modules/sw-toolbox/sw-toolbox.js');


// custom caching rules follow below


// prefer fresh data from the api endpoint
toolbox.router.get(/api.py/, toolbox.networkFirst);


// prefer fastest response for static resources
//   (This strategy queries both the cache and the network. Usually the
//   the cache answers faster, if the response is already cached. A benefit
//   of this strategy is that the cache will be updated when the network
//   request returns eventually).
toolbox.router.get(/node_modules/, toolbox.fastest);
toolbox.router.get(/html$/, toolbox.fastest);
toolbox.router.get(/resources/, toolbox.fastest);
toolbox.router.get(/^https:\/\/gravatar.com\//, toolbox.fastest);
