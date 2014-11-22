class Filetypes(object):
    PLUGINS = {}

    @classmethod
    def plugin(cls, extensions):
        def register(plugin):
            cls.PLUGINS[plugin] = map(lambda x: x.lower(), extensions)
        return register
