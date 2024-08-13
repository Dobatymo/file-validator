from typing import Tuple

from ..plug import Filetypes


@Filetypes.plugin(["py", "pyw"])
class Python:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with open(path, "rb") as fr:
                compile(fr.read(), "<file>", "exec")
            return (0, "")
        except (SyntaxError, TypeError) as e:
            return (1, str(e))
