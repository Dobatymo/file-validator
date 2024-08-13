from typing import Dict, Protocol, Set, Tuple, Type


class Plugin(Protocol):
    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]: ...


class PluginError(Exception):
    pass


class Filetypes:
    PLUGINS: Dict[Type, Set[str]] = {}

    @classmethod
    def plugin(cls, extensions):
        def register(plugin):
            cls.PLUGINS[plugin] = {x.lower() for x in extensions}
            return plugin

        return register
