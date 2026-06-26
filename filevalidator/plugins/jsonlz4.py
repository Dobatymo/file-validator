import json
from typing import Dict, Optional

import lz4.block

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size
from ..plug import Filetypes, ValidationResult

MAGIC = b"mozLz40\0"


@Filetypes.plugin(["jsonlz4"])
class JSONLZ4:
    def __init__(
        self,
        max_file_size: Optional[int] = DEFAULT_MAX_FILE_SIZE,
        max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
    ) -> None:
        self.max_file_size = max_file_size
        self.max_file_size_by_extension = max_file_size_by_extension

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        size_result = check_file_size(file_size, ext, self.max_file_size, self.max_file_size_by_extension)
        if size_result:
            return size_result

        try:
            with open(path, "rb") as fr:
                data = fr.read()
            if not data.startswith(MAGIC):
                return (1, "Missing jsonlz4 magic header")
            json.loads(lz4.block.decompress(data[len(MAGIC) :]).decode("utf-8"))
            return (0, "")
        except OSError:
            raise
        except Exception as e:
            return (1, str(e))
