import os

class ExtensionManager:
    """Manages extensions"""

    def __init__(self):
        """loads extensions"""

        self.extensions = []

        extensions_folder = "extensions"
        for extension_folder in os.listdir(extensions_folder):
            if os.path.isfile(extensions_folder + "/" + extension_folder + "/__init__.py"):
                mod = __import__("extensions." + extension_folder, fromlist=["Extension"])
                self.extensions.append(getattr(mod, "Extension")())


    def call_all(self, method, params):
        """invokes a method on all extensions"""

        for extension in self.extensions:
            method_pointer = getattr(extension, method, None)
            if method_pointer != None:
                method_pointer(*params)
