class Cache:
    """Cache"""

    cache = {}

    def put(self, entity_type, key, value):
        """adds an entry to the cache"""

        if not entity_type in self.cache:
            self.cache[entity_type] = {}
        self.cache[entity_type][key] = value


    def get(self, entity_type, key):
        """gets an entry from the cache"""

        if not entity_type in self.cache:
            return None
        return self.cache[entity_type][key]


    def has(self, entity_type, key):
        """checks whether an item is in the cache"""

        if not entity_type in self.cache:
            return False
        return key in self.cache[entity_type]
