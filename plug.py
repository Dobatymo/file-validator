from typing import Dict, Protocol, Set, Tuple, Type


class Plugin(Protocol):
    def validate(self, path, ext):
        # type: (str, str) -> Tuple[int, str]
        ...


class Filetypes:
    PLUGINS = {}  # type: Dict[Type, Set[str]]

    @classmethod
    def plugin(cls, extensions):
        def register(plugin):
            cls.PLUGINS[plugin] = {x.lower() for x in extensions}

        return register
