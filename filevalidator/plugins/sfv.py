import re
from typing import Tuple

from ..plug import Filetypes


@Filetypes.plugin(["sfv"])
class SFV:
    def __init__(self) -> None:
        self.p = re.compile(r"^(.* [a-fA-F0-9]{8}|;.*|)\n?$")

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        with open(path, encoding="latin1") as fr:
            for line in fr:
                m = self.p.match(line)
                if m is None:
                    return (1, f"Line doesn't match: `{line}`")
        return (0, "")
