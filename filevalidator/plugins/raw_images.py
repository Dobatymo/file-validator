from typing import Tuple

import rawpy

from ..plug import Filetypes


@Filetypes.plugin(["dng", "nef", "cr2", "cr3", "arw"])
class RawImages:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with rawpy.imread(path):
                pass
            return (0, "")
        except rawpy.LibRawError as e:
            return (1, str(e))
        except rawpy.NotSupportedError as e:
            return (-1, str(e))
