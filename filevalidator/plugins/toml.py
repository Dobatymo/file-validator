from typing import Tuple

import toml

from ..plug import Filetypes


@Filetypes.plugin(["toml"])
class TOML:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with open(path, encoding="utf-8") as fr:
                toml.load(fr)
            return (0, "")
        except toml.TomlDecodeError as e:
            return (1, str(e))
