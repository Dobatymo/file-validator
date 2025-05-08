from typing import Tuple

from ..plug import Filetypes


@Filetypes.plugin(["m3u8"])
class M3U8:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with open(path, encoding="utf-8") as fr:
                for _line in fr:
                    pass
            return (0, "")
        except UnicodeDecodeError as e:
            return (1, f"UnicodeDecodeError: {e}")
