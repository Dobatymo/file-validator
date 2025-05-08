import codecs
import re
from typing import Tuple

from ..plug import Filetypes


@Filetypes.plugin(["cue"])
class CUE:
    # https://web.archive.org/web/20151023011544/http://digitalx.org/cue-sheet/syntax/index.html

    def __init__(self) -> None:
        _fields = (
            "CATALOG",
            "CDTEXTFILE",
            "FILE",
            "FLAGS",
            "INDEX",
            "ISRC",
            "PERFORMER",
            "POSTGAP",
            "PREGAP",
            "REM",
            "SONGWRITER",
            "TITLE",
            "TRACK",
        )
        fields = "|".join(_fields)
        self.p = re.compile(f"(?i)^ *({fields}) .+$")
        self.codecs = {
            codecs.BOM_UTF8: "utf-8-sig",
            codecs.BOM_UTF16_BE: "utf-16-be",
            codecs.BOM_UTF16_LE: "utf-16-le",
            codecs.BOM_UTF32_BE: "utf-32-be",
            codecs.BOM_UTF32_LE: "utf-32-le",
        }

    def get_encoding(self, path: str, default: str = "latin1") -> str:
        with open(path, "rb") as fr:
            magic = fr.read(4)

        for bom, encoding in self.codecs.items():
            if magic[: len(bom)] == bom:
                return encoding
        return default

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        encoding = self.get_encoding(path)

        with open(path, encoding=encoding) as fr:
            for i, line in enumerate(fr, 1):
                stripped = line.rstrip()

                if not stripped:
                    continue

                m = self.p.match(stripped)
                if m is None:
                    return (1, f"Line {i} doesn't start with cue keyword: {stripped!r}")
        return (0, "")
