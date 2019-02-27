class Filetypes(object):
    PLUGINS = {}

    @classmethod
    def plugin(cls, extensions):
        def register(plugin):
            cls.PLUGINS[plugin] = list(x.lower() for x in extensions)
        return register
