from typing import Tuple

from genutility.json import read_json

from ..plug import Filetypes


@Filetypes.plugin(["json", "dtrashinfo"])
class JSON:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            read_json(path)
            return (0, "")
        except Exception as e:
            return (1, str(e))
