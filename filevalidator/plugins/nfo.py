import re
from pathlib import Path
from typing import Tuple

from ..plug import Filetypes

# non printables except \t \n \r
nonprintable_p = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]")  # 30 chars, 30 / 256 = 0.1171875


@Filetypes.plugin(["nfo"])
class NFO:
    """Plugin to verify scene .nfo files (not Microsoft Windows .nfo files)"""

    def __init__(self, ratio: float = 0.05) -> None:
        self.min_ratio = ratio

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        for encoding, errors in [
            ("ascii", "strict"),
            ("utf-8", "strict"),
            ("utf-16", "strict"),
            ("cp437", "strict"),
        ]:
            try:
                with Path(path).open("r", encoding=encoding, errors=errors) as fr:
                    data = fr.read()
                nonprintable = "".join(m.group(0) for m in nonprintable_p.finditer(data))
                if nonprintable:
                    ratio = len(nonprintable) / len(data)
                    if ratio < self.min_ratio:
                        return (
                            0,
                            f"Contains non printable characters (under {self.min_ratio}) ({len(nonprintable)}/{len(data)}): {nonprintable!r}",
                        )
                    elif ratio >= self.min_ratio:
                        return (
                            1,
                            f"Contains non printable characters (over {self.min_ratio}) ({len(nonprintable)}/{len(data)}): {nonprintable!r}",
                        )
                return (0, "")
            except (UnicodeDecodeError, UnicodeError):
                pass

        assert False
