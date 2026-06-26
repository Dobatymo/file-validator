import re
from pathlib import Path
from typing import Dict, Optional

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size
from ..plug import Filetypes, ValidationResult

# non printables except \t \n \r
nonprintable_p = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]")  # 30 chars, 30 / 256 = 0.1171875


@Filetypes.plugin(["nfo"])
class NFO:
    """Plugin to verify scene .nfo files (not Microsoft Windows .nfo files)"""

    def __init__(
        self,
        ratio: float = 0.05,
        max_file_size: Optional[int] = DEFAULT_MAX_FILE_SIZE,
        max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
    ) -> None:
        self.min_ratio = ratio
        self.max_file_size = max_file_size
        self.max_file_size_by_extension = max_file_size_by_extension

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        size_result = check_file_size(file_size, ext, self.max_file_size, self.max_file_size_by_extension)
        if size_result:
            return size_result

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
