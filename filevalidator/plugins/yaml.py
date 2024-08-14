from typing import Tuple

import yaml

from ..plug import Filetypes


@Filetypes.plugin(["yaml"])
class YAML:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with open(path, encoding="utf-8") as fr:
                yaml.safe_load(fr)
            return (0, "")
        except yaml.YAMLError as e:
            return (1, str(e))
