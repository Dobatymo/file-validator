from typing import Tuple

from genutility.json import read_json

from plug import Filetypes


@Filetypes.plugin(["json"])
class JSON:
    def __init__(self):
        pass

    def validate(self, path, ext):
        # type: (str, str) -> Tuple[int, str]

        try:
            read_json(path)
            return (0, "")
        except Exception as e:
            return (1, str(e))
