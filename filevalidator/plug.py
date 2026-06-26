from typing import Dict, Protocol, Set, Tuple, Type

ValidationResult = Tuple[int, str]


class Plugin(Protocol):
    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult: ...


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
