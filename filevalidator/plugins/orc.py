from typing import Tuple

from pyarrow import orc
from pyarrow.lib import ArrowException

from ..plug import Filetypes


@Filetypes.plugin(["orc"])
class ORC:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            orc.read_table(path)
            return (0, "")
        except ArrowException as e:
            return (1, str(e))
        except OSError as e:
            return (1, str(e))
